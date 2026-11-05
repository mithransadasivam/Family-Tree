from django.test import TestCase

from config.testing import client_for, join, make_tree, make_user
from family_members.models import FamilyMember


class PrivatePhoneBypassTests(TestCase):
    """C2: linking yourself to a person (`user`) must not unlock their private phone number."""

    def setUp(self):
        self.owner = make_user('owner')
        self.snoop = make_user('snoop')
        self.tree = make_tree(self.owner)
        join(self.tree, self.snoop)
        self.member = FamilyMember.objects.create(
            tree=self.tree, first_name='Gran', phone='555-9999', phone_public=False,
            created_by=self.owner)

    def test_member_cannot_link_themselves_to_read_a_private_phone(self):
        c = client_for(self.snoop)
        res = c.patch(f'/api/family-members/{self.member.id}/', {'user': self.snoop.id}, format='json')
        self.assertEqual(res.status_code, 400)
        self.member.refresh_from_db()
        self.assertIsNone(self.member.user_id)
        self.assertEqual(c.get(f'/api/family-members/{self.member.id}/').json()['phone'], '')

    def test_member_cannot_link_someone_else(self):
        res = client_for(self.snoop).patch(
            f'/api/family-members/{self.member.id}/', {'user': self.owner.id}, format='json')
        self.assertEqual(res.status_code, 400)

    def test_cannot_create_a_person_already_linked_to_oneself_to_read_the_phone(self):
        res = client_for(self.snoop).post('/api/family-members/', {
            'tree': self.tree.id, 'first_name': 'Fake', 'phone': '555-1', 'user': self.snoop.id,
        }, format='json')
        self.assertEqual(res.status_code, 201)
        created = FamilyMember.objects.get(id=res.json()['id'])
        self.assertIsNone(created.user_id)

    def test_owner_still_sees_private_phone(self):
        res = client_for(self.owner).get(f'/api/family-members/{self.member.id}/')
        self.assertEqual(res.json()['phone'], '555-9999')

    def test_unchanged_user_link_can_be_resent(self):
        self.member.user = self.owner
        self.member.save()
        res = client_for(self.owner).patch(
            f'/api/family-members/{self.member.id}/',
            {'user': self.owner.id, 'first_name': 'Gran2'}, format='json')
        self.assertEqual(res.status_code, 200)

    def test_only_the_owner_can_clear_or_set_the_link(self):
        self.member.user = self.owner
        self.member.save()
        url = f'/api/family-members/{self.member.id}/'
        self.assertEqual(client_for(self.snoop).patch(url, {'user': None}, format='json').status_code, 400)
        self.assertEqual(client_for(self.owner).patch(url, {'user': None}, format='json').status_code, 200)
        self.assertEqual(client_for(self.owner).patch(url, {'user': self.snoop.id}, format='json').status_code, 200)
        self.member.refresh_from_db()
        self.assertEqual(self.member.user_id, self.snoop.id)

    def test_owner_cannot_link_a_user_outside_the_tree(self):
        stranger = make_user('stranger')
        res = client_for(self.owner).patch(
            f'/api/family-members/{self.member.id}/', {'user': stranger.id}, format='json')
        self.assertEqual(res.status_code, 400)


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
