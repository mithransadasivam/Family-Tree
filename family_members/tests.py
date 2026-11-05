from django.test import TestCase

from config.testing import client_for, join, make_tree, make_user
from family_members.models import FamilyMember


class MemberTreeImmutableTests(TestCase):
    """C1: a member must never be movable into (or out of) another tree via PATCH."""

    def setUp(self):
        self.attacker = make_user('attacker')
        self.victim = make_user('victim')
        self.my_tree = make_tree(self.attacker, 'Mine')
        self.victim_tree = make_tree(self.victim, 'Victims')
        self.member = FamilyMember.objects.create(
            tree=self.my_tree, first_name='Pat', created_by=self.attacker)

    def test_cannot_move_member_into_someone_elses_tree(self):
        res = client_for(self.attacker).patch(
            f'/api/family-members/{self.member.id}/', {'tree': self.victim_tree.id}, format='json')
        self.assertEqual(res.status_code, 400)
        self.member.refresh_from_db()
        self.assertEqual(self.member.tree_id, self.my_tree.id)
        self.assertFalse(FamilyMember.objects.filter(tree=self.victim_tree).exists())

    def test_cannot_move_member_into_another_tree_even_if_also_a_member(self):
        other = make_tree(self.victim, 'Shared')
        join(other, self.attacker)
        res = client_for(self.attacker).patch(
            f'/api/family-members/{self.member.id}/', {'tree': other.id}, format='json')
        self.assertEqual(res.status_code, 400)
        self.member.refresh_from_db()
        self.assertEqual(self.member.tree_id, self.my_tree.id)

    def test_sending_the_same_tree_is_harmless(self):
        res = client_for(self.attacker).patch(
            f'/api/family-members/{self.member.id}/',
            {'tree': self.my_tree.id, 'first_name': 'Patricia'}, format='json')
        self.assertEqual(res.status_code, 200)
        self.member.refresh_from_db()
        self.assertEqual(self.member.first_name, 'Patricia')
