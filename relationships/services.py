"""
The one place relationships are created, changed and removed.

Who may do it is NOT decided here: the caller has already authorised the request (the normal
views check tree membership and, for delete, ownership; the staff views check IsSuperuser). What
every caller gets from here, identically: input validation, the per-tree lock, the sanity rules
(one link per pair, no parent loops), a refusal to write to a deleted tree, and a history entry.

`staff=True` is passed only by the staff views. It changes how the change is RECORDED, never what
is allowed: the history rows are flagged and labelled "Staff edit", and carry the detail an owner
needs to see what a superuser did (a snapshot on create and delete, one row per changed field on
update), plus a matching line in the `kinship.staff` server log. It is a keyword the views set, not
something a request body can influence.
"""
from django.db import IntegrityError, transaction

from edit_history.utils import as_json, log_edit, log_staff_change
from family_trees.models import FamilyTree
from utils.errors import ServiceError

from .models import Relationship
from .rules import check_relationship
from .serializers import RelationshipSerializer

TREE_DELETED = 'This family was deleted by its owner and can no longer be edited.'


def pair_taken_error():
    """The database's one-link-per-pair constraint fired (rules.py normally catches this first)."""
    return ServiceError(
        {'error': 'These two people are already connected. A pair can only have one relationship, '
                  'so edit or remove the existing one first.'},
        400,
    )


def lock_tree(tree_id):
    """
    Row-lock the tree for the rest of the current transaction. Relationship writes check the
    whole tree (one link per pair, no parent loops) and then save, so two at once must take
    turns or both can pass the check. Call inside transaction.atomic(). Refuses a deleted tree.
    """
    tree = FamilyTree.objects.select_for_update().get(id=tree_id)
    if not tree.is_active:
        raise ServiceError({'error': TREE_DELETED}, 409)
    return tree


def _name(member):
    return f'{member.first_name} {member.last_name}'.strip()


def describe(rel):
    """'Ann is the Father of Ben' - the way a stored link reads."""
    return f'{_name(rel.member_1)} is the {rel.relationship_type.type_name} of {_name(rel.member_2)}'


def snapshot(rel):
    """Everything worth knowing about a link, as plain data (ids and names, nothing private)."""
    return {
        'id': rel.id,
        'member_1': rel.member_1_id, 'member_1_name': _name(rel.member_1),
        'member_2': rel.member_2_id, 'member_2_name': _name(rel.member_2),
        'type': rel.relationship_type.type_name,
        'reads': describe(rel),
    }


def _changes(before, after):
    """[(field, label, old, new)] for what differs between two snapshots."""
    out = []
    for n in ('member_1', 'member_2'):
        if before[n] != after[n]:
            out.append((n, f'{n.replace("_", " ")}',
                        f'{before[n + "_name"]} (#{before[n]})', f'{after[n + "_name"]} (#{after[n]})'))
    if before['type'] != after['type']:
        out.append(('relationship_type', 'type', before['type'], after['type']))
    return out


def create_relationship(tree_id, data, actor, staff=False):
    tree_id = int(tree_id)
    serializer = RelationshipSerializer(data=data)
    if not serializer.is_valid():
        raise ServiceError(serializer.errors, 400)
    valid = serializer.validated_data
    if valid['tree'].id != tree_id:
        raise ServiceError({'tree': ['This is not the family being edited']}, 400)
    with transaction.atomic():
        tree = lock_tree(tree_id)
        problem = check_relationship(tree_id, valid['member_1'], valid['member_2'], valid['relationship_type'])
        if problem:
            raise ServiceError({'error': problem}, 400)
        try:
            with transaction.atomic():
                rel = serializer.save(created_by=actor)
        except IntegrityError:
            raise pair_taken_error()
        snap = snapshot(rel)
        log_edit(tree, 'relationship', rel.id, actor, f'Added relationship: {snap["reads"]}',
                 new_value=as_json(snap) if staff else '', by_staff=staff)
    if staff:
        log_staff_change(actor, tree, 'create', 'relationship', rel.id, ('member_1', 'member_2', 'relationship_type'))
    return rel


def update_relationship(rel, data, actor, staff=False):
    """Change a relationship's type and/or either member. The tree itself cannot change."""
    rel_id, tree_id = rel.id, rel.tree_id
    allowed = ('member_1', 'member_2', 'relationship_type')
    payload = {k: data[k] for k in allowed if k in data}
    changed = []
    with transaction.atomic():
        # Serialise with every other write to this tree, then re-read the link: it may have
        # been changed or removed while we waited for the lock.
        tree = lock_tree(tree_id)
        try:
            rel = Relationship.objects.select_related('member_1', 'member_2', 'relationship_type').get(id=rel_id)
        except Relationship.DoesNotExist:
            raise ServiceError({'error': 'Not found'}, 404)
        before = snapshot(rel)
        serializer = RelationshipSerializer(rel, data=payload, partial=True)
        if not serializer.is_valid():
            raise ServiceError(serializer.errors, 400)
        # Both people must belong to this relationship's own tree.
        for field in ('member_1', 'member_2'):
            member = serializer.validated_data.get(field)
            if member is not None and member.tree_id != rel.tree_id:
                raise ServiceError({'error': 'Member is not in this tree'}, 400)
        member_1 = serializer.validated_data.get('member_1', rel.member_1)
        member_2 = serializer.validated_data.get('member_2', rel.member_2)
        rel_type = serializer.validated_data.get('relationship_type', rel.relationship_type)
        problem = check_relationship(rel.tree_id, member_1, member_2, rel_type, exclude_id=rel.id)
        if problem:
            raise ServiceError({'error': problem}, 400)
        try:
            with transaction.atomic():
                rel = serializer.save()
        except IntegrityError:
            raise pair_taken_error()
        after = snapshot(rel)
        if not staff:
            log_edit(tree, 'relationship', rel.id, actor, f'Updated relationship: {after["reads"]}')
        else:
            changed = _changes(before, after)
            for field, label, old, new in changed:
                log_edit(tree, 'relationship', rel.id, actor, f'Changed {label} of a relationship: {after["reads"]}',
                         field_name=field, old_value=old, new_value=new, by_staff=True)
            if not changed:
                log_edit(tree, 'relationship', rel.id, actor, f'Saved a relationship with no changes: {after["reads"]}',
                         by_staff=True)
    if staff:
        log_staff_change(actor, tree, 'update', 'relationship', rel.id, [c[0] for c in changed])
    return rel


def delete_relationship(rel, actor, staff=False):
    with transaction.atomic():
        tree = lock_tree(rel.tree_id)
        try:
            rel = Relationship.objects.select_related('member_1', 'member_2', 'relationship_type').get(id=rel.id)
        except Relationship.DoesNotExist:
            raise ServiceError({'error': 'Not found'}, 404)
        snap = snapshot(rel)
        rel.delete()
        log_edit(tree, 'relationship', snap['id'], actor, f'Removed relationship: {snap["reads"]}',
                 old_value=as_json(snap) if staff else '', by_staff=staff)
    if staff:
        log_staff_change(actor, tree, 'delete', 'relationship', snap['id'])
