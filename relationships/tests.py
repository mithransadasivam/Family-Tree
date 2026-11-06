from unittest import mock

from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.db.models.query import QuerySet
from django.test import TestCase, TransactionTestCase

from config.testing import client_for, join, make_tree, make_user
from family_members.models import FamilyMember
from family_trees.models import FamilyTree
from relationships import services as rel_services
from relationships.models import Relationship, RelationshipType


class RelationshipWriteLockTests(TestCase):
    """
    C7: the "already connected" and "would loop" checks read the tree's relationships and the
    insert/update follows. Two simultaneous writes could both pass the check and then both save
    (two links for one pair, or a parent loop). Writes must therefore be serialised per tree:
    lock the tree row inside a fresh transaction BEFORE checking.

    SQLite cannot show real lock contention, so this asserts the contract: when the check runs,
    the tree row has already been locked, inside a new transaction.
    """

    def setUp(self):
        self.user = make_user('owner')
        self.tree = make_tree(self.user)
        mk = lambda n: FamilyMember.objects.create(tree=self.tree, first_name=n, created_by=self.user)
        self.a, self.b, self.c = mk('A'), mk('B'), mk('C')
        self.father = RelationshipType.objects.create(type_name='Father', category='biological')
        self.client = client_for(self.user)
        self.base_depth = len(connection.savepoint_ids)

    def record_write_ordering(self):
        events = []
        real_lock = QuerySet.select_for_update
        real_check = rel_services.check_relationship

        def lock(qs, *args, **kwargs):
            events.append(('lock', qs.model))
            return real_lock(qs, *args, **kwargs)

        def check(*args, **kwargs):
            events.append(('check', len(connection.savepoint_ids) > self.base_depth))
            return real_check(*args, **kwargs)

        return events, mock.patch.object(QuerySet, 'select_for_update', autospec=True, side_effect=lock), \
            mock.patch.object(rel_services, 'check_relationship', side_effect=check)

    def assertLockedThenChecked(self, events):
        self.assertIn(('lock', FamilyTree), events)
        self.assertLess(events.index(('lock', FamilyTree)), events.index(('check', True)),
                        f'tree must be locked, inside a transaction, before the check: {events}')

    def test_create_locks_the_tree_before_checking(self):
        events, p_lock, p_check = self.record_write_ordering()
        with p_lock, p_check:
            res = self.client.post('/api/relationships/', {
                'tree': self.tree.id, 'member_1': self.a.id, 'member_2': self.b.id,
                'relationship_type': self.father.id}, format='json')
        self.assertEqual(res.status_code, 201, res.content)
        self.assertLockedThenChecked(events)

    def test_edit_locks_the_tree_before_checking(self):
        rel = Relationship.objects.create(
            tree=self.tree, member_1=self.a, member_2=self.b, relationship_type=self.father)
        events, p_lock, p_check = self.record_write_ordering()
        with p_lock, p_check:
            res = self.client.patch(f'/api/relationships/{rel.id}/', {'member_2': self.c.id}, format='json')
        self.assertEqual(res.status_code, 200, res.content)
        self.assertLockedThenChecked(events)

    def test_second_write_for_the_same_pair_is_rejected(self):
        body = {'tree': self.tree.id, 'member_1': self.a.id, 'member_2': self.b.id,
                'relationship_type': self.father.id}
        self.assertEqual(self.client.post('/api/relationships/', body, format='json').status_code, 201)
        reverse = {**body, 'member_1': self.b.id, 'member_2': self.a.id}
        self.assertEqual(self.client.post('/api/relationships/', reverse, format='json').status_code, 400)
        self.assertEqual(Relationship.objects.filter(tree=self.tree).count(), 1)

    def test_a_parent_loop_is_rejected(self):
        for m1, m2 in ((self.a, self.b), (self.b, self.c)):
            self.assertEqual(self.client.post('/api/relationships/', {
                'tree': self.tree.id, 'member_1': m1.id, 'member_2': m2.id,
                'relationship_type': self.father.id}, format='json').status_code, 201)
        res = self.client.post('/api/relationships/', {
            'tree': self.tree.id, 'member_1': self.c.id, 'member_2': self.a.id,
            'relationship_type': self.father.id}, format='json')
        self.assertEqual(res.status_code, 400)
        self.assertIn('own ancestor', res.json()['error'])


class RelationshipEditTests(TestCase):
    """C5: an edit must be one atomic PATCH, so a rejected edit leaves the original link intact
    (the Android app used to delete the link first and then create a replacement)."""

    def setUp(self):
        self.user = make_user('owner')
        self.tree = make_tree(self.user)
        mk = lambda n: FamilyMember.objects.create(tree=self.tree, first_name=n, created_by=self.user)
        self.dad, self.kid, self.uncle = mk('Dad'), mk('Kid'), mk('Uncle')
        self.father = RelationshipType.objects.create(type_name='Father', category='biological')
        self.brother = RelationshipType.objects.create(type_name='Brother', category='biological')
        self.client = client_for(self.user)
        self.rel = Relationship.objects.create(
            tree=self.tree, member_1=self.dad, member_2=self.kid,
            relationship_type=self.father, created_by=self.user)
        # Dad and Uncle are already connected.
        Relationship.objects.create(
            tree=self.tree, member_1=self.dad, member_2=self.uncle, relationship_type=self.brother)

    def url(self):
        return f'/api/relationships/{self.rel.id}/'

    def test_rejected_edit_keeps_the_original_relationship(self):
        res = self.client.patch(self.url(), {
            'member_1': self.dad.id, 'member_2': self.uncle.id, 'relationship_type': self.father.id,
        }, format='json')
        self.assertEqual(res.status_code, 400)
        self.assertIn('already connected', res.json()['error'])
        self.rel.refresh_from_db()
        self.assertEqual((self.rel.member_1_id, self.rel.member_2_id), (self.dad.id, self.kid.id))
        self.assertEqual(self.rel.relationship_type_id, self.father.id)

    def test_successful_edit_updates_in_place_and_keeps_direction(self):
        res = self.client.patch(self.url(), {
            'member_1': self.dad.id, 'member_2': self.kid.id, 'relationship_type': self.brother.id,
        }, format='json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['id'], self.rel.id)
        self.rel.refresh_from_db()
        self.assertEqual((self.rel.member_1_id, self.rel.member_2_id), (self.dad.id, self.kid.id))
        self.assertEqual(self.rel.relationship_type_id, self.brother.id)
        self.assertEqual(self.rel.created_by_id, self.user.id)

    def test_non_member_cannot_edit(self):
        outsider = make_user('outsider')
        res = client_for(outsider).patch(
            self.url(), {'relationship_type': self.brother.id}, format='json')
        self.assertEqual(res.status_code, 403)


class OnePairOneRelationshipConstraintTests(TestCase):
    """C7 follow-up: the database itself refuses a second link between the same two people, in
    either direction, so even a missed lock or a direct write cannot create one."""

    def setUp(self):
        self.user = make_user('owner')
        self.tree = make_tree(self.user)
        mk = lambda n, t=None: FamilyMember.objects.create(tree=t or self.tree, first_name=n, created_by=self.user)
        self.a, self.b, self.c = mk('A'), mk('B'), mk('C')
        self.father = RelationshipType.objects.create(type_name='Father', category='biological')
        self.brother = RelationshipType.objects.create(type_name='Brother', category='biological')
        Relationship.objects.create(
            tree=self.tree, member_1=self.a, member_2=self.b, relationship_type=self.father)

    def make(self, m1, m2, tree=None, rtype=None):
        return Relationship.objects.create(
            tree=tree or self.tree, member_1=m1, member_2=m2, relationship_type=rtype or self.brother)

    def test_same_direction_duplicate_is_refused(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.make(self.a, self.b)

    def test_reverse_direction_duplicate_is_refused(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.make(self.b, self.a)

    def test_different_pairs_are_fine(self):
        self.make(self.a, self.c)
        self.make(self.c, self.b)
        self.assertEqual(Relationship.objects.count(), 3)

    def test_an_edit_that_would_duplicate_a_pair_is_refused(self):
        other = self.make(self.a, self.c)
        other.member_2 = self.b
        with self.assertRaises(IntegrityError), transaction.atomic():
            other.save()

    def test_api_turns_a_constraint_hit_into_a_clean_400_not_a_500(self):
        # Simulate the application-level check missing a duplicate (e.g. a lost race).
        client = client_for(self.user)
        with mock.patch.object(rel_services, 'check_relationship', return_value=None):
            res = client.post('/api/relationships/', {
                'tree': self.tree.id, 'member_1': self.b.id, 'member_2': self.a.id,
                'relationship_type': self.brother.id}, format='json')
            self.assertEqual(res.status_code, 400, res.content)
            self.assertIn('already connected', res.json()['error'])
            mine = self.make(self.a, self.c)
            res = client.patch(f'/api/relationships/{mine.id}/', {'member_2': self.b.id}, format='json')
            self.assertEqual(res.status_code, 400, res.content)
        self.assertEqual(Relationship.objects.count(), 2)


class UniquePairMigrationTests(TransactionTestCase):
    """The migration must apply on top of existing (duplicate-free) data and be reversible."""

    app = 'relationships'
    before = [('relationships', '0001_initial')]

    def test_migration_applies_to_existing_rows_and_reverses(self):
        executor = MigrationExecutor(connection)
        executor.migrate(self.before)
        old = executor.loader.project_state(self.before).apps
        # Only Relationship comes from the OLD schema state (no constraint yet); the people and
        # tree are ordinary rows made with the real models.
        Rel = old.get_model('relationships', 'Relationship')
        u = make_user('migrator')
        t = make_tree(u)
        a, b, c = (FamilyMember.objects.create(tree=t, first_name=n, created_by=u) for n in 'ABC')
        rt = RelationshipType.objects.create(type_name='Brother', category='biological')
        Rel.objects.create(tree_id=t.id, member_1_id=a.id, member_2_id=b.id, relationship_type_id=rt.id)
        Rel.objects.create(tree_id=t.id, member_1_id=c.id, member_2_id=a.id, relationship_type_id=rt.id)

        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes('relationships'))
        self.assertEqual(Relationship.objects.count(), 2)  # nothing lost
        with self.assertRaises(IntegrityError), transaction.atomic():
            Relationship.objects.create(
                tree_id=t.id, member_1_id=b.id, member_2_id=a.id, relationship_type_id=rt.id)

        executor = MigrationExecutor(connection)
        executor.migrate(self.before)  # reversible
        with transaction.atomic():
            Rel.objects.create(tree_id=t.id, member_1_id=b.id, member_2_id=a.id, relationship_type_id=rt.id)  # allowed again
        executor = MigrationExecutor(connection)
        Rel.objects.filter(member_1_id=b.id, member_2_id=a.id).delete()  # leave the DB clean for later tests
        executor.migrate(executor.loader.graph.leaf_nodes('relationships'))
