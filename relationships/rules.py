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


# member_1 and member_2 are a couple, so they belong to the same generation.
SPOUSE_TYPES = {'Spouse', 'Husband', 'Wife', 'Partner', 'Fiance', 'Fiancee'}

# Same lists as the website (web/src/graph.ts): a link "X is the Father of Y" says X is male.
MALE_TYPES = {
    'Father', 'Stepfather', 'Step Father', 'Grandfather', 'Son', 'Stepson', 'Step Son', 'Adopted Son',
    'Grandson', 'Brother', 'Step Brother', 'Adopted Brother', 'Husband', 'Fiance', 'Uncle',
    'Father-in-Law', 'Son-in-Law', 'Brother-in-Law',
}
FEMALE_TYPES = {
    'Mother', 'Stepmother', 'Step Mother', 'Grandmother', 'Daughter', 'Stepdaughter', 'Step Daughter',
    'Adopted Daughter', 'Granddaughter', 'Sister', 'Step Sister', 'Adopted Sister', 'Wife', 'Fiancee',
    'Aunt', 'Mother-in-Law', 'Daughter-in-Law', 'Sister-in-Law',
}


def ancestor_edge(type_name, member_1_id, member_2_id):
    """(ancestor_id, descendant_id) if this link is a parent/child kind, else None."""
    if type_name in PARENT_TYPES:
        return member_1_id, member_2_id
    if type_name in CHILD_TYPES:
        return member_2_id, member_1_id
    return None


def spouse_pair(type_name, member_1_id, member_2_id):
    """(a, b) if this link joins a couple, else None."""
    return (member_1_id, member_2_id) if type_name in SPOUSE_TYPES else None


def generation_conflict_members(ancestor_edges, couples):
    """Ids of the people caught in a generation contradiction. See generation_conflicts."""
    return generation_conflicts(ancestor_edges, couples)[1]


def generation_conflicts(ancestor_edges, couples):
    """
    (bad_edges, people): the parent links that sit on a contradiction about WHICH GENERATION
    people are in, and the people on them.

    Every link pins down generations: a couple share one, and a parent is above their child. A
    tree is only drawable if all of that can be true at once. Merge each couple into one node;
    then any parent link that runs from a node back to itself, or round a loop of nodes, is
    impossible. Example: Ann is Ben's father, Ben is Cara's father, and Ann and Cara are a couple
    - no parent loop on its own, but Cara would be both Ann's partner and her own grandchild's
    ancestor. A link stored the wrong way round (see H1) is the usual cause.

    ancestor_edges: iterable of (ancestor_id, descendant_id); couples: iterable of (id, id).
    bad_edges is a set of those (ancestor_id, descendant_id) pairs.
    """
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in couples:
        parent[find(a)] = find(b)
    edges = list(ancestor_edges)
    people = {x for e in edges for x in e} | {x for c in couples for x in c}
    for x in people:
        find(x)

    out, selfish = {}, set()
    for anc, desc in edges:
        ca, cd = find(anc), find(desc)
        if ca == cd:
            selfish.add(ca)
        else:
            out.setdefault(ca, set()).add(cd)

    # Strongly connected components (iterative Tarjan): any component of 2+ nodes is a loop.
    index, low, on_stack, stack, comp_of, counter = {}, {}, set(), [], {}, [0]
    nodes = {find(x) for x in people}
    for root in nodes:
        if root in index:
            continue
        work = [(root, iter(out.get(root, ())))]
        index[root] = low[root] = counter[0]
        counter[0] += 1
        stack.append(root)
        on_stack.add(root)
        while work:
            node, it = work[-1]
            advanced = False
            for nxt in it:
                if nxt not in index:
                    index[nxt] = low[nxt] = counter[0]
                    counter[0] += 1
                    stack.append(nxt)
                    on_stack.add(nxt)
                    work.append((nxt, iter(out.get(nxt, ()))))
                    advanced = True
                    break
                if nxt in on_stack:
                    low[node] = min(low[node], index[nxt])
            if advanced:
                continue
            work.pop()
            if work:
                low[work[-1][0]] = min(low[work[-1][0]], low[node])
            if low[node] == index[node]:
                members = []
                while True:
                    w = stack.pop()
                    on_stack.discard(w)
                    members.append(w)
                    if w == node:
                        break
                for w in members:
                    comp_of[w] = (node, len(members))

    bad_nodes = {n for n in nodes if comp_of[n][1] > 1} | selfish
    bad_edges = {
        (a, d) for a, d in edges
        if find(a) == find(d) or (find(a) in bad_nodes and comp_of[find(a)][0] == comp_of[find(d)][0])
    }
    return bad_edges, {x for x in people if find(x) in bad_nodes}


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

    # Generations must still add up once couples count as one. The loop check above ignores spouse
    # links, so it cannot see a contradiction that runs through a couple. Only refuse when THIS
    # link newly causes one, so a tree with an old contradiction can still be edited and repaired.
    new_couple = spouse_pair(rel_type.type_name, member_1.id, member_2.id)
    if edge or new_couple:
        edges, couples = [], []
        others = Relationship.objects.filter(tree_id=tree_id).select_related('relationship_type')
        if exclude_id is not None:
            others = others.exclude(id=exclude_id)
        for r in others:
            e = ancestor_edge(r.relationship_type.type_name, r.member_1_id, r.member_2_id)
            if e:
                edges.append(e)
            c = spouse_pair(r.relationship_type.type_name, r.member_1_id, r.member_2_id)
            if c:
                couples.append(c)
        before, _ = generation_conflicts(edges, couples)
        after, _ = generation_conflicts(edges + ([edge] if edge else []),
                                        couples + ([new_couple] if new_couple else []))
        # Judge by parent links newly on a loop, not by people: someone married into an already
        # broken part of the tree has not been put in a NEW contradiction.
        newly = {x for pair in after - before for x in pair}
        if after - before:
            from family_members.models import FamilyMember
            listed = ', '.join(sorted(_name(m) for m in FamilyMember.objects.filter(id__in=newly))[:4])
            return (
                f'That link does not fit the rest of the family ({listed}): a couple belong to the same '
                'generation and a parent is one generation above their child, but these links together '
                'say otherwise. Check whether an existing link between these people was entered the '
                'wrong way round.'
            )
    return None
