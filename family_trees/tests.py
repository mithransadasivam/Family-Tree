from django.test import TestCase

from communities.models import Community, CommunityMember, CommunityTree
from config.testing import client_for, join, make_tree, make_user
from edit_history.utils import log_edit
from family_codes.models import FamilyCode
from family_members.models import FamilyMember
from family_trees.models import TreeMember
from relationships.models import Relationship, RelationshipType
from users.models import UserProfile

PRIVATE_KEYS = {'phone', 'address', 'profile', 'created_at'}


class DeletedTreeTests(TestCase):
    """C4: a soft-deleted tree (is_active=False) must be unreachable and unsearchable."""

    def setUp(self):
        self.owner = make_user('owner')
        self.member = make_user('member')
        self.joiner = make_user('joiner')
        self.tree = make_tree(self.owner, 'Gone', approval_required=False)
        join(self.tree, self.member)
        self.a = FamilyMember.objects.create(tree=self.tree, first_name='Ann', created_by=self.owner)
        self.b = FamilyMember.objects.create(tree=self.tree, first_name='Bob', created_by=self.owner)
        self.rel_type = RelationshipType.objects.create(type_name='Brother', category='biological')
        self.rel = Relationship.objects.create(
            tree=self.tree, member_1=self.a, member_2=self.b, relationship_type=self.rel_type)
        self.code = FamilyCode.objects.create(tree=self.tree, code='GONE123456', created_by=self.owner)
        self.community = Community.objects.create(name='Village', owner=self.owner)
        CommunityMember.objects.create(community=self.community, user=self.owner, role='owner')
        CommunityTree.objects.create(community=self.community, tree=self.tree, added_by=self.owner)
        res = client_for(self.owner).delete(f'/api/family-trees/{self.tree.id}/')
        self.assertEqual(res.status_code, 200)

    def test_members_and_relationships_are_unreachable(self):
        c = client_for(self.member)
        t = self.tree.id
        self.assertEqual(c.get(f'/api/family-members/?tree_id={t}').status_code, 403)
        self.assertEqual(c.get(f'/api/family-members/{self.a.id}/').status_code, 403)
        self.assertEqual(c.patch(f'/api/family-members/{self.a.id}/', {'first_name': 'X'}, format='json').status_code, 403)
        self.assertEqual(c.post('/api/family-members/', {'tree': t, 'first_name': 'New'}, format='json').status_code, 403)
        self.assertEqual(c.delete(f'/api/family-members/{self.b.id}/').status_code, 403)
        self.assertEqual(c.get(f'/api/relationships/?tree_id={t}').status_code, 403)
        self.assertEqual(c.delete(f'/api/relationships/{self.rel.id}/').status_code, 403)
        self.assertEqual(c.get(f'/api/edit-history/?tree_id={t}').status_code, 403)
        self.a.refresh_from_db()
        self.assertEqual(self.a.first_name, 'Ann')
        self.assertTrue(Relationship.objects.filter(id=self.rel.id).exists())

    def test_codes_cannot_be_generated_or_redeemed(self):
        self.assertEqual(client_for(self.owner).post(
            '/api/family-codes/generate/', {'tree_id': self.tree.id}, format='json').status_code, 404)
        self.assertEqual(client_for(self.joiner).post(
            '/api/family-codes/redeem/', {'code': self.code.code}, format='json').status_code, 404)
        self.assertEqual(client_for(self.joiner).post(
            '/api/join-requests/', {'code': self.code.code}, format='json').status_code, 404)
        self.assertFalse(TreeMember.objects.filter(tree=self.tree, user=self.joiner).exists())

    def test_people_vanish_from_community_search(self):
        c = client_for(self.owner)
        res = c.get(f'/api/communities/{self.community.id}/people/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['count'], 0)
        self.assertFalse(CommunityTree.objects.filter(tree=self.tree).exists())

    def test_search_ignores_an_inactive_tree_even_if_still_shared(self):
        CommunityTree.objects.create(community=self.community, tree=self.tree, added_by=self.owner)
        res = client_for(self.owner).get(f'/api/communities/{self.community.id}/people/')
        self.assertEqual(res.json()['count'], 0)


class OwnerPrivacyTests(TestCase):
    """C3: nested user objects must not leak the owner's/editors' phone, address or profile."""

    def setUp(self):
        self.owner = make_user('owner')
        UserProfile.objects.create(user=self.owner, bio='secret bio', phone='555-7', location='Home')
        self.member = make_user('member')
        self.tree = make_tree(self.owner, 'Family', approval_required=False)
        join(self.tree, self.member)

    def assertNoPrivateData(self, user_json):
        self.assertTrue(PRIVATE_KEYS.isdisjoint(user_json), user_json)
        self.assertNotIn('555-0100', str(user_json))
        self.assertNotIn('street', str(user_json))
        # What the clients actually need is still there.
        self.assertEqual(user_json['id'] in (self.owner.id, self.member.id), True)
        self.assertIn('first_name', user_json)

    def test_tree_list_and_detail_hide_owner_private_details(self):
        c = client_for(self.member)
        self.assertNoPrivateData(c.get('/api/family-trees/').json()[0]['owner'])
        self.assertNoPrivateData(c.get(f'/api/family-trees/{self.tree.id}/').json()['owner'])

    def test_edit_history_hides_editor_private_details(self):
        log_edit(self.tree, 'family_member', 1, self.owner, 'Added member')
        rows = client_for(self.member).get(f'/api/edit-history/?tree_id={self.tree.id}').json()
        self.assertTrue(rows)
        for row in rows:
            self.assertNoPrivateData(row['edited_by'])

    def test_redeeming_a_code_does_not_reveal_the_owner_details(self):
        newcomer = make_user('newcomer')
        FamilyCode.objects.create(tree=self.tree, code='ABC123', created_by=self.owner)
        res = client_for(newcomer).post('/api/family-codes/redeem/', {'code': 'ABC123'}, format='json')
        self.assertEqual(res.status_code, 200, res.content)
        self.assertNoPrivateData(res.json()['tree']['owner'])

    def test_own_account_endpoint_still_returns_everything(self):
        me = client_for(self.owner).get('/api/users/me/').json()
        self.assertEqual(me['phone'], '555-0100')
        self.assertIn('profile', me)
