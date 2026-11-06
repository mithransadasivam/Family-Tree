"""
The one place people are created, changed and removed (see relationships/services.py: the caller
has already decided WHO may do it; this decides whether the write itself is allowed and records it).

`staff=True` (set only by the staff views) changes how a change is recorded, not what is allowed:
see relationships/services.py. A person's phone number is never written to any log or snapshot.
"""
from django.db import transaction
from django.db.models import Q

from edit_history.utils import as_json, log_edit, log_staff_change
from family_trees.models import FamilyTree
from relationships.rules import CHILD_TYPES, PARENT_TYPES
from relationships.services import TREE_DELETED, lock_tree, snapshot as link_snapshot
from utils.errors import ServiceError

from .models import FamilyMember
from .serializers import FamilyMemberSerializer, can_see_phone

# What a snapshot / field-level history may contain. Deliberately NOT phone or phone_public (private).
AUDIT_FIELDS = (
    'first_name', 'last_name', 'gender', 'email', 'address', 'photo_url',
    'birth_date', 'birth_place', 'death_date', 'death_place', 'user',
)
FIELD_LABELS = {
    'first_name': 'first name', 'last_name': 'last name', 'birth_date': 'birth date',
    'birth_place': 'birthplace', 'death_date': 'death date', 'death_place': 'death place',
    'photo_url': 'photo link', 'user': 'linked account',
}


def _name(member):
    return f'{member.first_name} {member.last_name}'


def snapshot(member):
    """The person's recordable details as plain data."""
    out = {}
    for f in AUDIT_FIELDS:
        value = member.user_id if f == 'user' else getattr(member, f)
        out[f] = None if value in (None, '') else str(value)
    return out


# A person who is the parent / grandparent of someone is a root of the tree: deleting them would
# orphan their descendants (see relationships/rules.py for how the types are read).
def has_descendants(member):
    from relationships.models import Relationship
    return (
        Relationship.objects.filter(
            member_1=member, relationship_type__type_name__in=PARENT_TYPES
        ).exists()
        or Relationship.objects.filter(
            member_2=member, relationship_type__type_name__in=CHILD_TYPES
        ).exists()
    )


def create_member(tree_id, data, actor, staff=False):
    tree_id = int(tree_id)
    serializer = FamilyMemberSerializer(data=data, context={'viewer': actor})
    if not serializer.is_valid():
        raise ServiceError(serializer.errors, 400)
    if serializer.validated_data['tree'].id != tree_id:
        raise ServiceError({'tree': ['This is not the family being edited']}, 400)
    with transaction.atomic():
        tree = FamilyTree.objects.get(id=tree_id)
        if not tree.is_active:
            raise ServiceError({'error': TREE_DELETED}, 409)
        member = serializer.save(created_by=actor)
        log_edit(tree, 'family_member', member.id, actor, f'Added member: {_name(member)}',
                 new_value=as_json(snapshot(member)) if staff else '', by_staff=staff)
    if staff:
        log_staff_change(actor, tree, 'create', 'member', member.id, [f for f, v in snapshot(member).items() if v])
    return member


def update_member(member, data, actor, staff=False):
    old_name = _name(member)
    before = snapshot(member)
    if not can_see_phone(member, actor):
        # Someone who cannot see a private number must not overwrite it or make it public.
        data = {k: v for k, v in data.items() if k not in ('phone', 'phone_public')}
    serializer = FamilyMemberSerializer(member, data=data, partial=True, context={'viewer': actor})
    if not serializer.is_valid():
        raise ServiceError(serializer.errors, 400)
    changed = []
    with transaction.atomic():
        if not member.tree.is_active:
            raise ServiceError({'error': TREE_DELETED}, 409)
        member = serializer.save()
        if not staff:
            log_edit(member.tree, 'family_member', member.id, actor, f'Updated member: {old_name}')
        else:
            after = snapshot(member)
            changed = [f for f in AUDIT_FIELDS if before[f] != after[f]]
            for f in changed:
                log_edit(member.tree, 'family_member', member.id, actor,
                         f'Changed {FIELD_LABELS.get(f, f)} of {old_name}',
                         field_name=f, old_value=before[f] or '', new_value=after[f] or '', by_staff=True)
            if not changed:
                log_edit(member.tree, 'family_member', member.id, actor,
                         f'Saved {old_name} with no changes', by_staff=True)
    if staff:
        log_staff_change(actor, member.tree, 'update', 'member', member.id, changed)
    return member


def delete_member(member, actor, staff=False):
    from relationships.models import Relationship
    with transaction.atomic():
        # Same lock as relationship writes: a link added while we check for children must not slip by.
        tree = lock_tree(member.tree_id)
        try:
            member = FamilyMember.objects.get(id=member.id)
        except FamilyMember.DoesNotExist:
            raise ServiceError({'error': 'Member not found'}, 404)
        if has_descendants(member):
            raise ServiceError(
                {'error': f'{member.first_name} has children in the family and cannot be deleted. '
                          'Remove their children (or those relationships) first.'},
                400,
            )
        name, member_id = _name(member), member.id
        # Deleting a person also deletes every link they are in. Capture them first so a staff
        # delete can say exactly what went with the person.
        links, stash = [], None
        if staff:
            rels = list(
                Relationship.objects.filter(Q(member_1=member) | Q(member_2=member))
                .select_related('member_1', 'member_2', 'relationship_type').order_by('id')
            )
            links = [link_snapshot(r) for r in rels]
            # Keep the whole row (private phone and account link included) so the delete can be undone
            # exactly. Written in this same transaction and BEFORE the delete: if it fails, nothing is deleted.
            from .restore import stash_member
            stash = stash_member(member, rels, actor)
        person = snapshot(member)
        member.delete()
        n = len(links)
        log_edit(tree, 'family_member', member_id, actor,
                 f'Deleted member: {name}' + (f' (and {n} relationship{"s" if n != 1 else ""})' if n else ''),
                 old_value=as_json({'member': person, 'relationships': links}) if staff else '', by_staff=staff)
        for link in links:
            log_edit(tree, 'relationship', link['id'], actor, f'Removed relationship: {link["reads"]} (with {name})',
                     old_value=as_json(link), by_staff=True)
    if staff:
        log_staff_change(actor, tree, 'delete', 'member', member_id,
                         [f'relationship_{link["id"]}' for link in links])
    return stash
