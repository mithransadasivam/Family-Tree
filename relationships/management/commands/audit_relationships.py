"""
Read-only audit of stored relationships. It never writes anything.

    python manage.py audit_relationships            # every tree, readable report
    python manage.py audit_relationships --tree 7   # one tree
    python manage.py audit_relationships --json     # machine-readable

It reports two kinds of problem, so each affected row can be reviewed and corrected by hand:

1. GENERATION CONTRADICTIONS - rows that cannot all be true together (a parent loop, or a loop that
   runs through a couple: spouses share a generation, a parent is above their child). Typical cause:
   a row stored the wrong way round by the Android app before the H1 fix (2026-11-04 20:48 PST).
2. GENDER CONTRADICTIONS - a row whose type says member_1 is male/female ("member_1 IS the Mother
   of member_2") but member_1's recorded gender is the opposite. When member_2 DOES match the type
   the row is flagged "likely stored backwards": swapping member_1 and member_2 would fix it.
"""
import json
from datetime import datetime, timezone

from django.core.management.base import BaseCommand

from family_trees.models import FamilyTree
from relationships.models import Relationship
from relationships.rules import (
    FEMALE_TYPES, MALE_TYPES, ancestor_edge, generation_conflicts, spouse_pair,
)

# Commit a13034e: new Android links follow the website's direction. Older rows may be reversed.
H1_FIX_AT = datetime(2026, 11, 5, 4, 48, 18, tzinfo=timezone.utc)


def _name(m):
    return f'{m.first_name} {m.last_name}'.strip() or f'#{m.id}'


def row_info(r):
    return {
        'id': r.id, 'member_1': r.member_1_id, 'member_1_name': _name(r.member_1),
        'type': r.relationship_type.type_name,
        'member_2': r.member_2_id, 'member_2_name': _name(r.member_2),
        'created_at': r.created_at.isoformat(),
        'before_h1_fix': r.created_at < H1_FIX_AT,
        'reads': f'{_name(r.member_1)} is the {r.relationship_type.type_name} of {_name(r.member_2)}',
    }


def audit_tree(rels):
    """rels: Relationship rows (with members and type loaded) of ONE tree -> findings dict."""
    edges, couples = [], []
    for r in rels:
        t = r.relationship_type.type_name
        e = ancestor_edge(t, r.member_1_id, r.member_2_id)
        if e:
            edges.append(e)
        c = spouse_pair(t, r.member_1_id, r.member_2_id)
        if c:
            couples.append(c)
    bad_edges, people = generation_conflicts(edges, couples)

    loops = []
    for r in rels:
        t = r.relationship_type.type_name
        e = ancestor_edge(t, r.member_1_id, r.member_2_id)
        is_parent_row = e in bad_edges if e else False
        # A couple row is part of the knot only if the knot loosens without it: a spouse link that
        # merely sits next to the contradiction is not a cause.
        is_couple_row = False
        c = spouse_pair(t, r.member_1_id, r.member_2_id)
        if c and r.member_1_id in people and r.member_2_id in people:
            rest = list(couples)
            rest.remove(c)
            is_couple_row = generation_conflicts(edges, rest)[0] != bad_edges
        if is_parent_row or is_couple_row:
            loops.append(row_info(r))

    genders = []
    for r in rels:
        t = r.relationship_type.type_name
        want = 'male' if t in MALE_TYPES else 'female' if t in FEMALE_TYPES else None
        have = r.member_1.gender
        if want and have in ('male', 'female') and have != want:
            info = row_info(r)
            info.update({'type_implies': want, 'member_1_recorded_gender': have,
                         'member_2_recorded_gender': r.member_2.gender or ''})
            # member_2 fits the type -> swapping the two people would make the row consistent.
            info['likely_stored_backwards'] = r.member_2.gender == want
            genders.append(info)
    return {'generation_contradictions': loops, 'gender_contradictions': genders}


class Command(BaseCommand):
    help = 'Read-only: list rows with generation (loop) or gender contradictions. Changes nothing.'

    def add_arguments(self, parser):
        parser.add_argument('--tree', type=int, help='Only this tree id')
        parser.add_argument('--json', action='store_true', help='Print JSON instead of text')

    def handle(self, *args, **opts):
        trees = FamilyTree.objects.all().order_by('id')
        if opts['tree']:
            trees = trees.filter(id=opts['tree'])
        report, total_trees = [], 0
        for tree in trees:
            total_trees += 1
            rels = list(Relationship.objects.filter(tree=tree)
                        .select_related('member_1', 'member_2', 'relationship_type').order_by('id'))
            found = audit_tree(rels)
            if found['generation_contradictions'] or found['gender_contradictions']:
                report.append({'tree_id': tree.id, 'tree_name': tree.tree_name,
                               'active': tree.is_active, **found})

        if opts['json']:
            self.stdout.write(json.dumps({'trees_checked': total_trees, 'trees_affected': len(report),
                                          'report': report}, indent=2, ensure_ascii=False))
            return
        out = self.stdout.write
        out(f'Checked {total_trees} tree(s); {len(report)} with findings. Nothing was changed.')
        for t in report:
            out('')
            out(f'== Tree {t["tree_id"]}: {t["tree_name"]}' + ('' if t['active'] else '  (deleted)'))
            if t['generation_contradictions']:
                out('  Generation contradictions (these rows cannot all be right; review each):')
                for r in t['generation_contradictions']:
                    flag = '  [created before H1 fix]' if r['before_h1_fix'] else ''
                    out(f'    row {r["id"]}: {r["reads"]}  ({r["created_at"][:10]}){flag}')
            if t['gender_contradictions']:
                out('  Gender contradictions (row says member_1 is one gender, profile says the other):')
                for r in t['gender_contradictions']:
                    hint = '  -> LIKELY STORED BACKWARDS: swap member_1 and member_2' \
                        if r['likely_stored_backwards'] else ''
                    flag = '  [created before H1 fix]' if r['before_h1_fix'] else ''
                    out(f'    row {r["id"]}: {r["reads"]}; {r["member_1_name"]} is recorded as '
                        f'{r["member_1_recorded_gender"]}, type implies {r["type_implies"]}'
                        f'  ({r["created_at"][:10]}){flag}{hint}')
