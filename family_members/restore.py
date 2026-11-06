"""
Staff-only undo for deleted people: stash the full row when a superuser deletes, put it back on request.

Why this exists: the website's own undo can only re-create what the person could see, and a superuser
cannot see a private phone number or set an account link, so that undo silently lost both. The stash
keeps the whole row (private columns included) for a limited time, so a restore is exact: same id,
same private phone, same account link, same links, same created-at.

Everything here is reached only from superuser-only views (family_trees/staff_write.py) and from the
staff delete in services.py. Nothing in this module is exposed to ordinary users, and the stash model
has no serializer and no admin page (see StaffDeletedMember).
"""
import json
from datetime import timedelta

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from edit_history.utils import as_json, log_edit, log_staff_change
from family_trees.models import TreeMember
from relationships.models import Relationship, RelationshipType
from relationships.rules import check_relationship
from relationships.services import describe, lock_tree
from users.models import User
from utils.errors import ServiceError

from .models import FamilyMember, StaffDeletedMember

# Every column of a person, private ones included. Deliberately a list rather than "all fields", so a
# column added later has to be chosen here on purpose.
PERSON_FIELDS = (
    'id', 'user_id', 'first_name', 'last_name', 'gender', 'phone', 'phone_public', 'email', 'address',
    'photo_url', 'birth_date', 'birth_place', 'death_date', 'death_place', 'created_by_id',
    'created_at', 'updated_at',
)
# Columns copied straight back (the rest need checks first, or are set by the database).
PLAIN_FIELDS = (
    'first_name', 'last_name', 'gender', 'phone', 'phone_public', 'email', 'address', 'photo_url',
    'birth_date', 'birth_place', 'death_date', 'death_place',
)


def retention():
    return timedelta(days=settings.STAFF_RESTORE_RETENTION_DAYS)


def purge_expired(now=None):
    """Delete every stash past its expiry. Returns how many went. Safe to call any time."""
    return StaffDeletedMember.objects.filter(expires_at__lte=now or timezone.now()).delete()[0]


def _exact(value):
    # isoformat keeps microseconds; DjangoJSONEncoder would cut timestamps to milliseconds.
    return value.isoformat() if hasattr(value, 'isoformat') else str(value)


def _dump(value):
    return json.dumps(value, default=_exact)


def stash_member(member, relationships, actor):
    """
    Keep `member` (a FamilyMember about to be deleted) and the links they are in. Call inside the
    delete's transaction and BEFORE the delete: if this fails the delete does not happen.
    """
    from relationships.services import snapshot as link_snapshot

    purge_expired()
    person = {f: getattr(member, f) for f in PERSON_FIELDS}
    links = [
        {**link_snapshot(r), 'relationship_type_id': r.relationship_type_id,
         'created_by_id': r.created_by_id, 'created_at': r.created_at}
        for r in relationships
    ]
    return StaffDeletedMember.objects.create(
        tree_id=member.tree_id,
        original_member_id=member.id,
        name=f'{member.first_name} {member.last_name}'.strip(),
        deleted_by=actor,
        expires_at=timezone.now() + retention(),
        person=_dump(person),
        links=_dump(links),
    )


def live_stashes(tree_id):
    """What can still be restored in this tree, newest first. Metadata only: never the person's data."""
    return StaffDeletedMember.objects.filter(tree_id=tree_id, expires_at__gt=timezone.now()).select_related('deleted_by')


def stash_summary(stash):
    who = stash.deleted_by
    return {
        'id': stash.id,
        'name': stash.name,
        'deleted_at': stash.deleted_at,
        'expires_at': stash.expires_at,
        'deleted_by': None if who is None else (f'{who.first_name} {who.last_name}'.strip() or who.email),
        'relationship_count': len(json.loads(stash.links)),
    }


def _live_stash(tree_id, stash_id):
    """The stash, or a clear refusal: 404 if there is none in this tree, 410 if it has expired."""
    stash = StaffDeletedMember.objects.filter(id=stash_id, tree_id=tree_id).first()
    if stash is None:
        raise ServiceError({'error': 'There is nothing to restore here (it may already have been restored).'}, 404)
    if stash.expires_at <= timezone.now():
        stash.delete()  # outside any atomic block of ours: the purge sticks even though we then refuse
        raise ServiceError({'error': 'This person was deleted too long ago to be restored.'}, 410)
    return stash


def _when(model, field, value):
    return model._meta.get_field(field).to_python(value) if value is not None else None


def restore_member(tree_id, stash_id, actor):
    """
    Put a staff-deleted person back exactly as they were. Returns a dict:
      member, restored_links (int), skipped_links ([{link, reason}]), account_link ('restored'|'dropped'|'none').
    Links that no longer fit (the other person was deleted, the pair is now connected, it would loop)
    are skipped and reported, never forced in. A deleted tree refuses (409) like every other write.
    """
    _live_stash(tree_id, stash_id)
    skipped, restored = [], []
    with transaction.atomic():
        tree = lock_tree(tree_id)
        stash = StaffDeletedMember.objects.select_for_update().filter(id=stash_id, tree_id=tree_id).first()
        if stash is None:  # restored by someone else while we waited for the lock
            raise ServiceError({'error': 'There is nothing to restore here (it may already have been restored).'}, 404)
        data, links = json.loads(stash.person), json.loads(stash.links)
        original_id = data['id']

        kwargs = {f: _when(FamilyMember, f, data[f]) for f in PLAIN_FIELDS}
        # The account link: only if that account is still in this family and not already someone else's card.
        account = 'none'
        uid = data['user_id']
        if uid is not None:
            ok = (TreeMember.objects.filter(tree_id=tree.id, user_id=uid).exists()
                  and not FamilyMember.objects.filter(tree_id=tree.id, user_id=uid).exists())
            kwargs['user_id'] = uid if ok else None
            account = 'restored' if ok else 'dropped'
        if data['created_by_id'] and User.objects.filter(id=data['created_by_id']).exists():
            kwargs['created_by_id'] = data['created_by_id']
        if not FamilyMember.objects.filter(id=original_id).exists():
            kwargs['id'] = original_id  # same id, so old history and links still point at the right person
        member = FamilyMember(tree_id=tree.id, **kwargs)
        member.save(force_insert=True)
        FamilyMember.objects.filter(pk=member.pk).update(created_at=_when(FamilyMember, 'created_at', data['created_at']))
        member.refresh_from_db()

        for link in links:
            m1_id = member.id if link['member_1'] == original_id else link['member_1']
            m2_id = member.id if link['member_2'] == original_id else link['member_2']
            rtype = RelationshipType.objects.filter(id=link['relationship_type_id']).first()
            m1 = member if m1_id == member.id else FamilyMember.objects.filter(id=m1_id, tree_id=tree.id).first()
            m2 = member if m2_id == member.id else FamilyMember.objects.filter(id=m2_id, tree_id=tree.id).first()
            if m1 is None or m2 is None:
                skipped.append({'link': link['reads'], 'reason': 'the other person is no longer in this family'})
                continue
            if rtype is None:
                skipped.append({'link': link['reads'], 'reason': 'that relationship type no longer exists'})
                continue
            problem = check_relationship(tree.id, m1, m2, rtype)
            if problem:
                skipped.append({'link': link['reads'], 'reason': problem})
                continue
            extra = {}
            if not Relationship.objects.filter(id=link['id']).exists():
                extra['id'] = link['id']
            if link['created_by_id'] and User.objects.filter(id=link['created_by_id']).exists():
                extra['created_by_id'] = link['created_by_id']
            try:
                with transaction.atomic():
                    rel = Relationship(tree_id=tree.id, member_1=m1, member_2=m2, relationship_type=rtype, **extra)
                    rel.save(force_insert=True)
            except IntegrityError:
                skipped.append({'link': link['reads'], 'reason': 'these two people are already connected'})
                continue
            Relationship.objects.filter(pk=rel.pk).update(created_at=_when(Relationship, 'created_at', link['created_at']))
            restored.append(rel)

        from .services import snapshot  # lazy: services imports this module

        name = f'{member.first_name} {member.last_name}'
        detail = f' with {len(restored)} of {len(links)} relationships' if links else ''
        log_edit(tree, 'family_member', member.id, actor, f'Restored member: {name}{detail}',
                 new_value=as_json(snapshot(member)), by_staff=True)
        for rel in restored:
            log_edit(tree, 'relationship', rel.id, actor, f'Restored relationship: {describe(rel)}', by_staff=True)
        for s in skipped:
            log_edit(tree, 'relationship', 0, actor, f'Could not restore relationship: {s["link"]} ({s["reason"]})',
                     by_staff=True)
        stash.delete()  # one-shot: the private data does not linger once it is back where it belongs
    purge_expired()  # tidy up any other expired stashes while we are here
    log_staff_change(actor, tree, 'restore', 'member', member.id,
                     [f'relationship_{r.id}' for r in restored] + [f'skipped_{i}' for i in range(len(skipped))])
    return {'member': member, 'restored_links': len(restored), 'skipped_links': skipped, 'account_link': account}
