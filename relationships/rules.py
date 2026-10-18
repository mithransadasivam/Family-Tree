"""
Sanity rules for relationships, shared by every client (web and Android).

A relationship row reads: "member_1 IS <type> OF member_2" (e.g. member_1 is the Father of
member_2). These checks stop contradictory or impossible links from being saved.
"""
from django.db.models import Q

# member_1 is a parent / grandparent of member_2 ...
PARENT_TYPES = {
    'Father', 'Mother', 'Stepfather', 'Stepmother', 'Step Father', 'Step Mother',
    'Grandfather', 'Grandmother',
}
# ... or member_1 is a child / grandchild of member_2.
CHILD_TYPES = {
    'Son', 'Daughter', 'Stepson', 'Stepdaughter', 'Step Son', 'Step Daughter',
    'Adopted Son', 'Adopted Daughter', 'Grandson', 'Granddaughter',
}


def ancestor_edge(type_name, member_1_id, member_2_id):
    """(ancestor_id, descendant_id) if this link is a parent/child kind, else None."""
    if type_name in PARENT_TYPES:
        return member_1_id, member_2_id
    if type_name in CHILD_TYPES:
        return member_2_id, member_1_id
    return None


def _name(member):
    return f'{member.first_name} {member.last_name}'.strip()


def check_relationship(tree_id, member_1, member_2, rel_type, exclude_id=None):
    """
    Return an error message if this relationship must not be saved, else None.

    - both people must exist in the same family as the relationship
    - nobody can be related to themselves
    - two people can have only ONE relationship between them (so nobody is both "Husband"
      and "Brother" of the same person), counting either direction
    - parent/child links cannot loop (nobody can become their own ancestor)
    """
    from .models import Relationship

    if member_1.id == member_2.id:
        return 'A person cannot be related to themselves'
    if member_1.tree_id != tree_id or member_2.tree_id != tree_id:
        return 'Both people must be in this family'

    same_pair = Relationship.objects.filter(tree_id=tree_id).filter(
        Q(member_1=member_1, member_2=member_2) | Q(member_1=member_2, member_2=member_1)
    )
    if exclude_id is not None:
        same_pair = same_pair.exclude(id=exclude_id)
    existing = same_pair.select_related('relationship_type').first()
    if existing:
        return (
            f'{_name(member_1)} and {_name(member_2)} are already connected '
            f'({existing.relationship_type.type_name}). A pair can only have one relationship, '
            'so edit or remove the existing one first.'
        )

    edge = ancestor_edge(rel_type.type_name, member_1.id, member_2.id)
    if edge:
        ancestor, descendant = edge
        # Would the person who is about to become a descendant already be an ancestor?
        children = {}
        others = Relationship.objects.filter(tree_id=tree_id).select_related('relationship_type')
        if exclude_id is not None:
            others = others.exclude(id=exclude_id)
        for r in others:
            e = ancestor_edge(r.relationship_type.type_name, r.member_1_id, r.member_2_id)
            if e:
                children.setdefault(e[0], set()).add(e[1])
        seen, stack = set(), [descendant]
        while stack:
            cur = stack.pop()
            if cur == ancestor:
                a = member_1 if ancestor == member_1.id else member_2
                d = member_2 if a is member_1 else member_1
                return f'That would make {_name(a)} their own ancestor: {_name(d)} is already above them in the family.'
            if cur in seen:
                continue
            seen.add(cur)
            stack.extend(children.get(cur, ()))
    return None
