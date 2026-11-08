"""
Generation contradictions: links that are each fine alone but cannot all be true together.

The real case (tree "Siva Sankar"): Sivananthan and Jayalakshmi are a couple, Sivasankaran is
Sivananthan's son, and an old Android build stored "Sivasankaran is the Mother of Jayalakshmi"
(the wrong way round). No parent loop exists on its own, because the spouse link is not a parent
link, so the old loop check passed it - yet it makes Jayalakshmi both Sivananthan's partner and
his grandchild's ancestor.
"""
from django.test import TestCase

from config.testing import client_for, make_tree, make_user
from family_members.models import FamilyMember
from relationships.models import Relationship, RelationshipType
from relationships.rules import generation_conflict_members


class GenerationConflictMembersTests(TestCase):
    def test_the_reported_shape_is_a_conflict(self):
        S, J, SK = 1, 2, 3
        self.assertEqual(generation_conflict_members([(S, SK), (SK, J)], [(S, J)]), {S, J, SK})

    def test_the_same_family_entered_correctly_is_fine(self):
        S, J, SK = 1, 2, 3
        self.assertEqual(generation_conflict_members([(S, SK), (J, SK)], [(S, J)]), set())

    def test_a_plain_parent_loop_is_a_conflict(self):
        self.assertEqual(generation_conflict_members([(1, 2), (2, 3), (3, 1)], []), {1, 2, 3})

    def test_parent_and_child_who_are_a_couple_is_a_conflict(self):
        self.assertEqual(generation_conflict_members([(1, 2)], [(1, 2)]), {1, 2})

    def test_unrelated_people_are_not_dragged_in(self):
        edges = [(1, 2), (2, 3), (3, 1), (10, 11)]
        self.assertEqual(generation_conflict_members(edges, [(10, 12)]), {1, 2, 3})

    def test_two_lineages_joined_by_marriage_are_fine(self):
        # Ann+Bob; their son Cal marries Dee, whose parents are Eve+Fox.
        edges = [(1, 3), (2, 3), (5, 4), (6, 4)]
        self.assertEqual(generation_conflict_members(edges, [(1, 2), (3, 4), (5, 6)]), set())


class GenerationConflictApiTests(TestCase):
    def setUp(self):
        self.user = make_user('owner')
        self.tree = make_tree(self.user)
        self.client = client_for(self.user)
        mk = lambda n, g='': FamilyMember.objects.create(tree=self.tree, first_name=n, gender=g, created_by=self.user)
        self.s, self.j, self.sk = mk('Sivananthan', 'male'), mk('Jayalakshmi', 'female'), mk('Sivasankaran', 'male')
        self.other = mk('Other')
        self.t = {n: RelationshipType.objects.create(type_name=n, category=c) for n, c in [
            ('Spouse', 'marriage'), ('Son', 'biological'), ('Mother', 'biological'),
            ('Father', 'biological'), ('Wife', 'marriage')]}
        self.link(self.s, 'Spouse', self.j)
        self.link(self.sk, 'Son', self.s)

    def link(self, a, type_name, b):
        return Relationship.objects.create(tree=self.tree, member_1=a, member_2=b,
                                           relationship_type=self.t[type_name], created_by=self.user)

    def post(self, a, type_name, b):
        return self.client.post('/api/relationships/', {
            'tree': self.tree.id, 'member_1': a.id, 'member_2': b.id,
            'relationship_type': self.t[type_name].id}, format='json')

    def test_the_backwards_mother_link_is_refused(self):
        res = self.post(self.sk, 'Mother', self.j)  # "Sivasankaran is the Mother of Jayalakshmi"
        self.assertEqual(res.status_code, 400)
        self.assertIn('does not fit the rest of the family', res.json()['error'])
        self.assertIn('Jayalakshmi', res.json()['error'])
        self.assertFalse(Relationship.objects.filter(member_1=self.sk, member_2=self.j).exists())

    def test_the_same_link_the_right_way_round_is_accepted(self):
        res = self.post(self.j, 'Mother', self.sk)  # "Jayalakshmi is the Mother of Sivasankaran"
        self.assertEqual(res.status_code, 201, res.content)

    def test_the_spouse_link_that_completes_the_contradiction_is_refused_too(self):
        # Same three people, but now the spouse link is the LAST one entered.
        Relationship.objects.filter(relationship_type=self.t['Spouse']).delete()
        self.link(self.sk, 'Mother', self.j)
        res = self.post(self.s, 'Spouse', self.j)
        self.assertEqual(res.status_code, 400)
        self.assertIn('does not fit the rest of the family', res.json()['error'])

    def test_a_pure_parent_loop_keeps_its_own_message(self):
        self.link(self.s, 'Son', self.other)  # Other > Sivananthan > Sivasankaran
        res = self.post(self.sk, 'Father', self.other)  # ... and Sivasankaran is Other's father
        self.assertEqual(res.status_code, 400)
        self.assertIn('their own ancestor', res.json()['error'])

    def test_a_tree_with_an_old_contradiction_can_still_be_edited(self):
        self.link(self.sk, 'Mother', self.j)  # the bad row, already in the data
        res = self.post(self.sk, 'Wife', self.other)  # unrelated and fine
        self.assertEqual(res.status_code, 201, res.content)

    def test_the_bad_row_can_be_repaired_by_editing_it(self):
        bad = self.link(self.sk, 'Mother', self.j)
        res = self.client.patch(f'/api/relationships/{bad.id}/',
                                {'member_1': self.j.id, 'member_2': self.sk.id}, format='json')
        self.assertEqual(res.status_code, 200, res.content)
        bad.refresh_from_db()
        self.assertEqual((bad.member_1_id, bad.member_2_id), (self.j.id, self.sk.id))
