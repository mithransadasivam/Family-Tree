from django.test import TestCase

from config.testing import client_for, join, make_tree, make_user
from edit_history.utils import log_edit
from family_codes.models import FamilyCode
from users.models import UserProfile

PRIVATE_KEYS = {'phone', 'address', 'profile', 'created_at'}


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
