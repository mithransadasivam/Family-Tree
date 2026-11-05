from unittest import mock

from django.db import connection
from django.db.models.query import QuerySet
from django.test import TestCase

from config.testing import client_for, join, make_tree, make_user
from family_members.models import FamilyMember
from family_trees.models import FamilyTree
from relationships import views as rel_views
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
        real_check = rel_views.check_relationship

        def lock(qs, *args, **kwargs):
            events.append(('lock', qs.model))
            return real_lock(qs, *args, **kwargs)

        def check(*args, **kwargs):
            events.append(('check', len(connection.savepoint_ids) > self.base_depth))
            return real_check(*args, **kwargs)

        return events, mock.patch.object(QuerySet, 'select_for_update', autospec=True, side_effect=lock), \
            mock.patch.object(rel_views, 'check_relationship', side_effect=check)

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
