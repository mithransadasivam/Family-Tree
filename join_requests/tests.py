import copy
from unittest import mock

from django.test import TestCase

from config.testing import client_for, make_tree, make_user
from family_codes.models import FamilyCode
from family_trees.models import TreeMember
from join_requests.models import JoinRequest

"""
C6: joining/approving must be race-safe.

The races are simulated deterministically: the stale copy is what a second request would have
read just before the first one committed. A correct implementation re-reads the row under a lock
inside a transaction (select_for_update), so it never acts on the stale copy. (SQLite has no row
locks, so these exercise the re-read logic rather than the lock itself.)
"""


def stale_get(model, **lookup):
    """Patch `model.objects.get` to keep returning the object as it is RIGHT NOW."""
    snapshot = model.objects.get(**lookup)
    # A fresh copy per call: each request has its own in-memory object, taken before any commit.
    return mock.patch.object(model.objects, 'get', side_effect=lambda **kw: copy.copy(snapshot))


class SingleUseCodeTests(TestCase):
    def setUp(self):
        self.owner = make_user('owner')
        self.first = make_user('first')
        self.second = make_user('second')
        self.tree = make_tree(self.owner, 'Open', approval_required=False)
        self.code = FamilyCode.objects.create(tree=self.tree, code='OPEN123456', created_by=self.owner)

    def test_redeem_cannot_use_a_code_a_concurrent_request_just_consumed(self):
        with stale_get(FamilyCode, code='OPEN123456'):
            res = client_for(self.first).post('/api/family-codes/redeem/', {'code': 'OPEN123456'}, format='json')
            self.assertEqual(res.status_code, 200)
            res = client_for(self.second).post('/api/family-codes/redeem/', {'code': 'OPEN123456'}, format='json')
        self.assertEqual(res.status_code, 400, res.content)
        self.assertFalse(TreeMember.objects.filter(tree=self.tree, user=self.second).exists())

    def test_join_request_auto_join_cannot_reuse_a_just_consumed_code(self):
        with stale_get(FamilyCode, code='OPEN123456'):
            res = client_for(self.first).post('/api/join-requests/', {'code': 'OPEN123456'}, format='json')
            self.assertEqual(res.status_code, 201)
            res = client_for(self.second).post('/api/join-requests/', {'code': 'OPEN123456'}, format='json')
        self.assertEqual(res.status_code, 400, res.content)
        self.assertFalse(TreeMember.objects.filter(tree=self.tree, user=self.second).exists())

    def test_losing_a_membership_race_is_a_clean_400_not_a_500(self):
        # The user already joined, but this request's "am I a member?" check ran before that.
        TreeMember.objects.create(tree=self.tree, user=self.first, role='member')
        real_filter = TreeMember.objects.filter

        def blind_filter(*args, **kwargs):
            qs = real_filter(*args, **kwargs)
            return mock.Mock(exists=lambda: False) if kwargs.get('user') == self.first else qs

        with mock.patch.object(TreeMember.objects, 'filter', side_effect=blind_filter):
            res = client_for(self.first).post('/api/join-requests/', {'code': 'OPEN123456'}, format='json')
        self.assertEqual(res.status_code, 400, res.content)
        self.assertEqual(TreeMember.objects.filter(tree=self.tree, user=self.first).count(), 1)


class ApproveRejectRaceTests(TestCase):
    def setUp(self):
        self.owner = make_user('owner')
        self.applicant = make_user('applicant')
        self.tree = make_tree(self.owner, 'Closed', approval_required=True)
        self.code = FamilyCode.objects.create(tree=self.tree, code='SHUT123456', created_by=self.owner)
        self.req = JoinRequest.objects.create(
            tree=self.tree, requester=self.applicant, status='pending', family_code_used=self.code)

    def patch(self, status_value):
        return client_for(self.owner).patch(
            f'/api/join-requests/{self.req.id}/', {'status': status_value}, format='json')

    def test_approve_after_a_concurrent_reject_does_not_add_the_member(self):
        with stale_get(JoinRequest, id=self.req.id):
            self.assertEqual(self.patch('rejected').status_code, 200)
            res = self.patch('approved')
        self.assertEqual(res.status_code, 400, res.content)
        self.req.refresh_from_db()
        self.assertEqual(self.req.status, 'rejected')
        self.assertFalse(TreeMember.objects.filter(tree=self.tree, user=self.applicant).exists())

    def test_reject_after_a_concurrent_approve_keeps_status_and_membership_consistent(self):
        with stale_get(JoinRequest, id=self.req.id):
            self.assertEqual(self.patch('approved').status_code, 200)
            res = self.patch('rejected')
        self.assertEqual(res.status_code, 400, res.content)
        self.req.refresh_from_db()
        self.assertEqual(self.req.status, 'approved')
        self.assertTrue(TreeMember.objects.filter(tree=self.tree, user=self.applicant).exists())

    def test_normal_approval_still_works_and_consumes_the_code(self):
        self.assertEqual(self.patch('approved').status_code, 200)
        self.code.refresh_from_db()
        self.assertTrue(self.code.is_used)
        self.assertTrue(TreeMember.objects.filter(tree=self.tree, user=self.applicant).exists())
