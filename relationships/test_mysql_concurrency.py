"""
Real-concurrency tests for the row locks added in C6 (join/approve) and C7 (relationship writes).

SQLite ignores SELECT ... FOR UPDATE, so the normal suite can only simulate these races. These tests
fire genuinely simultaneous requests from threads, each with its own MySQL connection, and only run
on MySQL (they skip elsewhere):

    python manage.py test relationships.test_mysql_concurrency     # config.settings = MySQL

Every locked scenario has a CONTROL run with the locks switched off. The control must reproduce the
race, otherwise the locked test proves nothing; if it cannot within a few rounds it is skipped
(not passed), so an inconclusive result is visible.
"""
import itertools
import threading
import time
from unittest import SkipTest, mock

from django.db import connection, connections
from django.db.models.query import QuerySet
from django.test import TransactionTestCase

from config.testing import client_for, make_tree, make_user
from family_codes.models import FamilyCode
from family_members.models import FamilyMember
from family_trees.models import TreeMember
from join_requests.models import JoinRequest
from relationships import views as rel_views
from relationships.models import Relationship, RelationshipType

CONTROL_ROUNDS = 10
_ids = itertools.count(1)


def run_together(jobs):
    """Run each callable in its own thread (own DB connection), released at the same instant."""
    barrier = threading.Barrier(len(jobs))
    results = [None] * len(jobs)

    def runner(i, job):
        try:
            barrier.wait()
            results[i] = job()
        except BaseException as exc:  # noqa: BLE001 - reported by the assertion, not the thread
            results[i] = exc
        finally:
            connections.close_all()

    threads = [threading.Thread(target=runner, args=(i, j)) for i, j in enumerate(jobs)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(60)
    return results


def statuses(results):
    return sorted(getattr(r, 'status_code', repr(r)) for r in results)


def linger(real, delay=0.05):
    """Wrap a function so it pauses after running, widening the check-then-save window."""
    def wrapper(*args, **kwargs):
        out = real(*args, **kwargs)
        time.sleep(delay)
        return out
    return wrapper


def no_locks():
    """select_for_update becomes a no-op: the code as it was before C6/C7."""
    return mock.patch.object(QuerySet, 'select_for_update', lambda self, *a, **k: self)


def slow_check():
    return mock.patch.object(rel_views, 'check_relationship', linger(rel_views.check_relationship))


def slow_join_save():
    """Pause just before a code is marked used (after the 'is it unused?' check)."""
    real_save = FamilyCode.save
    return mock.patch.object(FamilyCode, 'save', lambda self, *a, **k: (time.sleep(0.05), real_save(self, *a, **k))[1])


class MySQLRowLockTests(TransactionTestCase):
    def setUp(self):
        if connection.vendor != 'mysql':
            raise SkipTest('needs MySQL: SQLite has no row locks')

    # ---- C7: relationship writes -------------------------------------------------------------
    def relationship_jobs(self):
        n = next(_ids)
        owner = make_user(f'owner{n}')
        tree = make_tree(owner)
        a = FamilyMember.objects.create(tree=tree, first_name='A', created_by=owner)
        b = FamilyMember.objects.create(tree=tree, first_name='B', created_by=owner)
        father, _ = RelationshipType.objects.get_or_create(type_name='Father', category='biological')
        client = client_for(owner)

        def post(m1, m2):
            return lambda: client.post('/api/relationships/', {
                'tree': tree.id, 'member_1': m1.id, 'member_2': m2.id,
                'relationship_type': father.id}, format='json')
        # "A is Father of B" vs "B is Father of A", three of each, all at once: at most one may win.
        return tree, [post(a, b), post(b, a)] * 3

    def test_c7_simultaneous_relationship_writes_keep_one_link_per_pair(self):
        tree, jobs = self.relationship_jobs()
        with slow_check():
            results = run_together(jobs)
        self.assertEqual(statuses(results), [201, 400, 400, 400, 400, 400], results)
        self.assertEqual(Relationship.objects.filter(tree=tree).count(), 1)

    def test_c7_control_without_locks_the_race_is_real(self):
        for _ in range(CONTROL_ROUNDS):
            tree, jobs = self.relationship_jobs()
            with no_locks(), slow_check():
                run_together(jobs)
            if Relationship.objects.filter(tree=tree).count() > 1:
                return
        raise SkipTest('race not reproduced without locks: the locked test is not conclusive')

    # ---- C6: single-use code ------------------------------------------------------------------
    def code_jobs(self, path):
        n = next(_ids)
        owner = make_user(f'owner{n}')
        tree = make_tree(owner, 'Open', approval_required=False)
        FamilyCode.objects.create(tree=tree, code=f'RACE{n:06d}', created_by=owner)
        jobs = []
        for i in range(6):
            client = client_for(make_user(f'joiner{n}_{i}'))
            jobs.append(lambda c=client: c.post(path, {'code': f'RACE{n:06d}'}, format='json'))
        return tree, jobs

    def test_c6_single_use_code_admits_exactly_one_simultaneous_redeem(self):
        tree, jobs = self.code_jobs('/api/family-codes/redeem/')
        with slow_join_save():
            results = run_together(jobs)
        self.assertEqual(statuses(results), [200, 400, 400, 400, 400, 400], results)
        self.assertEqual(TreeMember.objects.filter(tree=tree, role='member').count(), 1)

    def test_c6_single_use_code_admits_exactly_one_simultaneous_join_request(self):
        tree, jobs = self.code_jobs('/api/join-requests/')
        with slow_join_save():
            results = run_together(jobs)
        self.assertEqual(statuses(results), [201, 400, 400, 400, 400, 400], results)
        self.assertEqual(TreeMember.objects.filter(tree=tree, role='member').count(), 1)

    def test_c6_control_without_locks_a_code_is_used_more_than_once(self):
        for _ in range(CONTROL_ROUNDS):
            tree, jobs = self.code_jobs('/api/family-codes/redeem/')
            with no_locks(), slow_join_save():
                run_together(jobs)
            if TreeMember.objects.filter(tree=tree, role='member').count() > 1:
                return
        raise SkipTest('race not reproduced without locks: the locked tests are not conclusive')

    # ---- C6: approve vs reject ----------------------------------------------------------------
    def approve_reject_jobs(self):
        n = next(_ids)
        owner, applicant = make_user(f'owner{n}'), make_user(f'applicant{n}')
        tree = make_tree(owner, 'Closed', approval_required=True)
        code = FamilyCode.objects.create(tree=tree, code=f'SHUT{n:06d}', created_by=owner)
        req = JoinRequest.objects.create(tree=tree, requester=applicant, family_code_used=code)
        c = client_for(owner)
        patch = lambda s: (lambda: c.patch(f'/api/join-requests/{req.id}/', {'status': s}, format='json'))
        return tree, req, applicant, [patch('approved'), patch('rejected')] * 3

    def test_c6_simultaneous_approve_and_reject_cannot_both_win(self):
        tree, req, applicant, jobs = self.approve_reject_jobs()
        with slow_join_save():
            results = run_together(jobs)
        self.assertEqual(statuses(results).count(200), 1, results)
        req.refresh_from_db()
        is_member = TreeMember.objects.filter(tree=tree, user=applicant).exists()
        self.assertEqual(req.status == 'approved', is_member, (req.status, is_member))

    def test_c6_control_without_locks_status_and_membership_can_disagree(self):
        for _ in range(CONTROL_ROUNDS):
            tree, req, applicant, jobs = self.approve_reject_jobs()
            with no_locks(), slow_join_save():
                results = run_together(jobs)
            req.refresh_from_db()
            is_member = TreeMember.objects.filter(tree=tree, user=applicant).exists()
            if statuses(results).count(200) > 1 or (req.status == 'approved') != is_member:
                return
        raise SkipTest('race not reproduced without locks: the locked test is not conclusive')
