"""Superuser-only read access to every tree (for browsing them in the website's staff pages)."""
import logging

from django.test import TestCase
from rest_framework.test import APIClient

from config.testing import client_for, join, make_tree, make_user
from edit_history.utils import log_edit
from family_members.models import FamilyMember
from family_trees.models import FamilyTree
from relationships.models import Relationship, RelationshipType
from users.models import User


def make_super(name='root'):
    return User.objects.create_superuser(email=f'{name}@example.com', google_id=f'g-{name}', password=None)


class StaffTreeSetup(TestCase):
    def setUp(self):
        self.owner = make_user('owner')
        self.member = make_user('member')
        self.tree = make_tree(self.owner, 'Smith Family')
        join(self.tree, self.member)
        self.ann = FamilyMember.objects.create(
            tree=self.tree, first_name='Ann', phone='555-1111', phone_public=False, created_by=self.owner)
        self.ben = FamilyMember.objects.create(
            tree=self.tree, first_name='Ben', phone='555-2222', phone_public=True, created_by=self.owner)
        rtype = RelationshipType.objects.create(type_name='Brother', category='biological')
        self.rel = Relationship.objects.create(
            tree=self.tree, member_1=self.ann, member_2=self.ben, relationship_type=rtype)
        self.other_owner = make_user('other')
        self.other_tree = make_tree(self.other_owner, 'Jones Family')
        self.root = make_super()
        self.url = '/api/staff/trees/'
        self.detail = f'/api/staff/trees/{self.tree.id}/'


class StaffAccessControlTests(StaffTreeSetup):
    def test_anonymous_is_refused(self):
        for url in (self.url, self.detail):
            self.assertEqual(APIClient().get(url).status_code, 401)

    def test_a_regular_user_is_refused_even_for_their_own_tree(self):
        for url in (self.url, self.detail):
            self.assertEqual(client_for(self.owner).get(url).status_code, 403)
            self.assertEqual(client_for(self.member).get(url).status_code, 403)

    def test_staff_without_superuser_is_refused(self):
        limited = make_user('limited')
        limited.is_staff = True
        limited.save()
        for url in (self.url, self.detail):
            self.assertEqual(client_for(limited).get(url).status_code, 403)

    def test_a_deactivated_superuser_is_refused(self):
        client = client_for(self.root)
        self.assertEqual(client.get(self.url).status_code, 200)
        self.root.is_active = False
        self.root.save()
        self.assertIn(client.get(self.url).status_code, (401, 403))

    def test_removing_the_flag_takes_effect_immediately(self):
        client = client_for(self.root)
        self.assertEqual(client.get(self.url).status_code, 200)
        self.root.is_superuser = False
        self.root.save()
        self.assertEqual(client.get(self.url).status_code, 403)

    def test_writes_are_not_allowed_even_for_a_superuser(self):
        c = client_for(self.root)
        for url in (self.url, self.detail):
            self.assertEqual(c.post(url, {}, format='json').status_code, 405)
            self.assertEqual(c.put(url, {}, format='json').status_code, 405)
            self.assertEqual(c.patch(url, {}, format='json').status_code, 405)
            self.assertEqual(c.delete(url).status_code, 405)
        self.assertTrue(FamilyTree.objects.filter(pk=self.tree.pk).exists())

    def test_the_normal_endpoints_still_refuse_a_superuser_who_is_not_a_member(self):
        # The bypass lives only in /api/staff/: nothing else was loosened.
        c = client_for(self.root)
        t = self.tree.id
        self.assertEqual(c.get(f'/api/family-members/?tree_id={t}').status_code, 403)
        self.assertEqual(c.get(f'/api/relationships/?tree_id={t}').status_code, 403)
        self.assertEqual(c.get(f'/api/family-trees/{t}/').status_code, 403)
        self.assertEqual(c.get(f'/api/edit-history/?tree_id={t}').status_code, 403)
        self.assertEqual(c.get('/api/family-trees/').json(), [])  # a member of nothing
        self.assertEqual(c.delete(f'/api/family-members/{self.ann.id}/').status_code, 403)

    def test_a_user_cannot_make_themselves_a_superuser(self):
        c = client_for(self.member)
        res = c.patch('/api/users/me/', {'is_superuser': True, 'is_staff': True}, format='json')
        self.assertEqual(res.status_code, 200)
        self.member.refresh_from_db()
        self.assertFalse(self.member.is_superuser or self.member.is_staff)
        self.assertEqual(c.get(self.url).status_code, 403)


class StaffTreeListTests(StaffTreeSetup):
    def test_lists_every_tree_with_owner_and_counts(self):
        res = client_for(self.root).get(self.url)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data['count'], 2)
        by_name = {t['tree_name']: t for t in data['results']}
        smith = by_name['Smith Family']
        self.assertEqual(smith['owner']['email'], 'owner@example.com')
        self.assertEqual(smith['account_count'], 2)  # owner + one joined account
        self.assertEqual(smith['people_count'], 2)   # Ann and Ben
        self.assertTrue(smith['is_active'])
        self.assertIn('created_at', smith)
        self.assertEqual(by_name['Jones Family']['people_count'], 0)

    def test_deleted_trees_are_listed_but_flagged(self):
        self.other_tree.is_active = False
        self.other_tree.save()
        data = client_for(self.root).get(self.url).json()
        flags = {t['tree_name']: t['is_active'] for t in data['results']}
        self.assertEqual(flags, {'Smith Family': True, 'Jones Family': False})

    def test_owner_is_shown_without_private_details(self):
        owner = client_for(self.root).get(self.url).json()['results'][0]['owner']
        self.assertTrue({'phone', 'address', 'profile'}.isdisjoint(owner), owner)

    def test_search_matches_tree_name_and_owner(self):
        c = client_for(self.root)
        names = lambda q: [t['tree_name'] for t in c.get(self.url + q).json()['results']]
        self.assertEqual(names('?q=smith'), ['Smith Family'])
        self.assertEqual(names('?q=other@'), ['Jones Family'])
        self.assertEqual(c.get(self.url + '?q=zzz').json()['count'], 0)

    def test_paging(self):
        for i in range(5):
            make_tree(self.owner, f'Extra {i}')
        c = client_for(self.root)
        data = c.get(self.url + '?limit=3&offset=2').json()
        self.assertEqual(data['count'], 7)
        self.assertEqual(len(data['results']), 3)
        self.assertEqual(c.get(self.url + '?limit=abc').status_code, 400)


class StaffTreeDetailTests(StaffTreeSetup):
    def test_returns_the_tree_with_its_people_and_relationships(self):
        res = client_for(self.root).get(self.detail)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data['tree']['tree_name'], 'Smith Family')
        self.assertEqual({m['first_name'] for m in data['members']}, {'Ann', 'Ben'})
        self.assertEqual([r['id'] for r in data['relationships']], [self.rel.id])
        self.assertEqual(data['relationships'][0]['relationship_type_name'], 'Brother')

    def test_private_phone_numbers_are_blanked_public_ones_shown(self):
        members = client_for(self.root).get(self.detail).json()['members']
        self.assertEqual({m['first_name']: m['phone'] for m in members}, {'Ann': '', 'Ben': '555-2222'})

    def test_works_for_a_deleted_tree(self):
        self.tree.is_active = False
        self.tree.save()
        self.assertEqual(client_for(self.root).get(self.detail).status_code, 200)

    def test_unknown_tree_is_404(self):
        self.assertEqual(client_for(self.root).get('/api/staff/trees/99999/').status_code, 404)

    def test_each_view_is_logged_with_who_and_which_tree(self):
        with self.assertLogs('kinship.staff', level=logging.INFO) as logs:
            client_for(self.root).get(self.detail)
            client_for(self.root).get(self.url)
        text = '\n'.join(logs.output)
        self.assertIn(f'user={self.root.id}', text)
        self.assertIn(f'tree={self.tree.id}', text)
        self.assertEqual(len(logs.output), 2)

    def test_viewing_writes_nothing_to_the_trees_edit_history(self):
        log_edit(self.tree, 'family_member', self.ann.id, self.owner, 'Added member: Ann')
        before = self.tree.edit_history.count()
        client_for(self.root).get(self.detail)
        self.assertEqual(self.tree.edit_history.count(), before)


class MeEndpointFlagsTests(StaffTreeSetup):
    def test_me_reports_the_accounts_own_flags(self):
        mine = client_for(self.root).get('/api/users/me/').json()
        self.assertTrue(mine['is_superuser'] and mine['is_staff'])
        plain = client_for(self.member).get('/api/users/me/').json()
        self.assertFalse(plain['is_superuser'] or plain['is_staff'])

    def test_other_peoples_flags_are_never_shown_to_anyone(self):
        # The owner other members see (tree list, edit history) is the public shape.
        owner_json = client_for(self.member).get('/api/family-trees/').json()[0]['owner']
        self.assertNotIn('is_superuser', owner_json)
        self.assertNotIn('is_staff', owner_json)
