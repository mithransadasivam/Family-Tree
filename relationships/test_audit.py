import io
import json

from django.core.management import call_command
from django.test import TestCase

from config.testing import make_tree, make_user
from family_members.models import FamilyMember
from relationships.models import Relationship, RelationshipType


class AuditRelationshipsTests(TestCase):
    def setUp(self):
        u = make_user('owner')
        self.u = u
        self.tree = make_tree(u, 'Siva Sankar')
        self.clean = make_tree(u, 'Clean')
        mk = lambda tree, n, g: FamilyMember.objects.create(tree=tree, first_name=n, gender=g, created_by=u)
        self.t = {n: RelationshipType.objects.create(type_name=n, category=c) for n, c in [
            ('Spouse', 'marriage'), ('Son', 'biological'), ('Mother', 'biological'), ('Father', 'biological')]}
        self.s, self.j, self.sk = mk(self.tree, 'Sivananthan', 'male'), mk(self.tree, 'Jayalakshmi', 'female'), \
            mk(self.tree, 'Sivasankaran', 'male')
        self.link(self.tree, self.s, 'Spouse', self.j)
        self.link(self.tree, self.sk, 'Son', self.s)
        self.bad = self.link(self.tree, self.sk, 'Mother', self.j)  # stored backwards (row 134)
        a, b = mk(self.clean, 'A', 'male'), mk(self.clean, 'B', 'female')
        self.link(self.clean, a, 'Father', b)

    def link(self, tree, a, t, b):
        return Relationship.objects.create(tree=tree, member_1=a, member_2=b,
                                           relationship_type=self.t[t], created_by=self.u)

    def run_audit(self):
        out = io.StringIO()
        call_command('audit_relationships', '--json', stdout=out)
        return json.loads(out.getvalue())

    def test_flags_only_the_affected_tree_and_rows(self):
        data = self.run_audit()
        self.assertEqual((data['trees_checked'], data['trees_affected']), (2, 1))
        t = data['report'][0]
        self.assertEqual(t['tree_name'], 'Siva Sankar')
        loop_ids = {r['id'] for r in t['generation_contradictions']}
        self.assertIn(self.bad.id, loop_ids)
        self.assertEqual(len(loop_ids), 3)  # the spouse row and both parent rows form the knot

    def test_gender_row_is_flagged_as_likely_backwards(self):
        g = self.run_audit()['report'][0]['gender_contradictions']
        self.assertEqual([r['id'] for r in g], [self.bad.id])
        self.assertTrue(g[0]['likely_stored_backwards'])  # Sivasankaran is male, "Mother" implies female

    def test_it_changes_nothing(self):
        snap = lambda: list(Relationship.objects.order_by('id').values_list(
            'id', 'member_1', 'member_2', 'relationship_type'))
        before = snap()
        call_command('audit_relationships', stdout=io.StringIO())
        self.run_audit()
        self.assertEqual(before, snap())

    def test_text_report_names_the_row(self):
        out = io.StringIO()
        call_command('audit_relationships', stdout=out)
        text = out.getvalue()
        self.assertIn(f'row {self.bad.id}: Sivasankaran is the Mother of Jayalakshmi', text)
        self.assertIn('LIKELY STORED BACKWARDS', text)
        self.assertNotIn(f'== Tree {self.clean.id}', text)
