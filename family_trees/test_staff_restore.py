"""
Staff-only server-side restore of deleted people (family_members/restore.py).

A superuser cannot see a private phone number or set an account link, so the website's own undo (which
re-sends what it was shown) silently loses both. The stash keeps the whole row, so restore is exact. These
tests pin: it IS exact, it degrades safely, it is reachable only by superusers and never shown to the
tree's owner or members, and it expires and cleans up.
"""
import json
from datetime import timedelta
from io import StringIO
from unittest import mock

from django.contrib import admin
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from config.testing import client_for, join, make_tree, make_user
from edit_history.models import EditHistory
from family_members.models import FamilyMember, StaffDeletedMember
from family_trees.models import FamilyTree, TreeMember
from family_trees.test_staff import make_super
from relationships.models import Relationship, RelationshipType

PHONE = '555-0123'


class RestoreSetup(TestCase):
    def setUp(self):
        self.owner = make_user('owner')
        self.member = make_user('member')
        self.ana_user = make_user('ana')
        self.tree = make_tree(self.owner, 'Smith Family')
        join(self.tree, self.member)
        join(self.tree, self.ana_user)
        mk = lambda n, **kw: FamilyMember.objects.create(tree=self.tree, first_name=n, last_name='Rao', created_by=self.owner, **kw)
        self.ugo, self.mia = mk('Ugo', gender='male'), mk('Mia', gender='female')
        self.ana = mk('Ana', gender='female', phone=PHONE, phone_public=False, user=self.ana_user,
                      birth_place='Pune', birth_date='1990-04-05')
        self.wife = RelationshipType.objects.create(type_name='Wife', category='marriage')
        self.sister = RelationshipType.objects.create(type_name='Sister', category='biological')
        self.l1 = Relationship.objects.create(tree=self.tree, member_1=self.ana, member_2=self.ugo,
                                              relationship_type=self.wife, created_by=self.owner)
        self.l2 = Relationship.objects.create(tree=self.tree, member_1=self.ana, member_2=self.mia,
                                              relationship_type=self.sister, created_by=self.member)
        self.root = make_super()
        self.c = client_for(self.root)
        self.base = f'/api/staff/trees/{self.tree.id}'
        self.ana_id, self.ana_created = self.ana.id, self.ana.created_at

    def delete_ana(self):
        res = self.c.delete(f'{self.base}/members/{self.ana_id}/')
        self.assertEqual(res.status_code, 200, res.content)
        return res.json()['restore_id']

    def restore(self, stash_id, client=None):
        return (client or self.c).post(f'{self.base}/restores/{stash_id}/', {}, format='json')

    def expire(self, stash_id):
        StaffDeletedMember.objects.filter(id=stash_id).update(expires_at=timezone.now() - timedelta(seconds=1))


class StashCreationTests(RestoreSetup):
    def test_a_staff_delete_stashes_the_whole_row_private_data_included(self):
        stash_id = self.delete_ana()
        stash = StaffDeletedMember.objects.get(id=stash_id)
        person = json.loads(stash.person)
        self.assertEqual((person['phone'], person['phone_public'], person['user_id']), (PHONE, False, self.ana_user.id))
        self.assertEqual((person['id'], person['birth_place'], person['first_name']), (self.ana_id, 'Pune', 'Ana'))
        self.assertEqual({link['id'] for link in json.loads(stash.links)}, {self.l1.id, self.l2.id})
        self.assertEqual((stash.tree_id, stash.deleted_by_id, stash.original_member_id), (self.tree.id, self.root.id, self.ana_id))

    def test_the_delete_response_carries_an_id_and_none_of_the_persons_data(self):
        res = self.c.delete(f'{self.base}/members/{self.ana_id}/')
        self.assertEqual(set(res.json()), {'message', 'restore_id'})
        self.assertNotIn(PHONE, res.content.decode())

    def test_the_stash_lasts_thirty_days_by_default_and_the_window_is_configurable(self):
        stash = StaffDeletedMember.objects.get(id=self.delete_ana())
        self.assertAlmostEqual((stash.expires_at - stash.deleted_at).total_seconds(), 30 * 86400, delta=60)
        mia_extra = FamilyMember.objects.create(tree=self.tree, first_name='Zed', created_by=self.owner)
        with override_settings(STAFF_RESTORE_RETENTION_DAYS=2):
            res = self.c.delete(f'{self.base}/members/{mia_extra.id}/')
        short = StaffDeletedMember.objects.get(id=res.json()['restore_id'])
        self.assertAlmostEqual((short.expires_at - short.deleted_at).total_seconds(), 2 * 86400, delta=60)

    def test_only_staff_deletes_are_stashed(self):
        client_for(self.owner).delete(f'/api/family-members/{self.ana_id}/')
        self.assertEqual(StaffDeletedMember.objects.count(), 0)

    def test_a_refused_delete_stashes_nothing(self):
        Relationship.objects.create(tree=self.tree, member_1=self.ugo, member_2=self.mia,
                                    relationship_type=RelationshipType.objects.create(type_name='Father', category='biological'))
        res = self.c.delete(f'{self.base}/members/{self.ugo.id}/')  # Ugo is Mia's father: has descendants
        self.assertEqual(res.status_code, 400)
        self.assertEqual(StaffDeletedMember.objects.count(), 0)

    def test_if_the_stash_cannot_be_written_the_delete_does_not_happen(self):
        with mock.patch('family_members.restore.StaffDeletedMember.objects.create', side_effect=RuntimeError('disk full')):
            with self.assertRaises(RuntimeError):
                self.c.delete(f'{self.base}/members/{self.ana_id}/')
        self.assertTrue(FamilyMember.objects.filter(id=self.ana_id).exists())
        self.assertEqual(Relationship.objects.count(), 2)


class RestoreExactnessTests(RestoreSetup):
    def test_everything_comes_back_exactly_including_private_phone_and_account_link(self):
        stash_id = self.delete_ana()
        res = self.restore(stash_id)
        self.assertEqual(res.status_code, 200, res.content)
        body = res.json()
        self.assertEqual((body['restored_relationships'], body['skipped_relationships'], body['account_link']),
                         (2, [], 'restored'))
        ana = FamilyMember.objects.get(id=self.ana_id)  # the SAME id
        self.assertEqual((ana.phone, ana.phone_public, ana.user_id), (PHONE, False, self.ana_user.id))
        self.assertEqual((ana.first_name, ana.last_name, ana.gender, ana.birth_place, str(ana.birth_date)),
                         ('Ana', 'Rao', 'female', 'Pune', '1990-04-05'))
        self.assertEqual(ana.created_at, self.ana_created)
        self.assertEqual(ana.created_by_id, self.owner.id)
        links = {r.id: (r.member_1_id, r.member_2_id, r.relationship_type_id, r.created_by_id)
                 for r in Relationship.objects.filter(tree=self.tree)}
        self.assertEqual(links, {
            self.l1.id: (self.ana_id, self.ugo.id, self.wife.id, self.owner.id),
            self.l2.id: (self.ana_id, self.mia.id, self.sister.id, self.member.id),
        })

    def test_the_restore_answer_still_hides_the_private_phone_from_staff(self):
        res = self.restore(self.delete_ana())
        self.assertEqual(res.json()['member']['phone'], '')
        self.assertNotIn(PHONE, res.content.decode())

    def test_the_owner_sees_the_private_phone_again_through_the_normal_endpoint(self):
        self.restore(self.delete_ana())
        people = client_for(self.owner).get(f'/api/family-members/?tree_id={self.tree.id}').json()
        self.assertEqual({p['first_name']: p['phone'] for p in people}['Ana'], PHONE)

    def test_it_is_one_shot_and_the_private_data_does_not_linger(self):
        stash_id = self.delete_ana()
        self.assertEqual(self.restore(stash_id).status_code, 200)
        self.assertFalse(StaffDeletedMember.objects.filter(id=stash_id).exists())
        again = self.restore(stash_id)
        self.assertEqual(again.status_code, 404)
        self.assertEqual(FamilyMember.objects.filter(first_name='Ana').count(), 1)

    def test_the_restore_is_recorded_as_a_labelled_staff_edit_without_the_phone(self):
        self.restore(self.delete_ana())
        rows = list(EditHistory.objects.filter(tree=self.tree).order_by('id'))
        restored = [r for r in rows if 'Restored' in r.change_description]
        self.assertEqual([r.change_description for r in restored], [
            'Staff edit: Restored member: Ana Rao with 2 of 2 relationships',
            'Staff edit: Restored relationship: Ana Rao is the Wife of Ugo Rao',
            'Staff edit: Restored relationship: Ana Rao is the Sister of Mia Rao',
        ])
        self.assertTrue(all(r.by_staff and r.edited_by_id == self.root.id for r in restored))
        self.assertNotIn(PHONE, ' '.join(f'{r.change_description} {r.old_value} {r.new_value}' for r in rows))

    def test_a_restore_logs_to_the_server_log_without_values(self):
        stash_id = self.delete_ana()
        with self.assertLogs('kinship.staff', level='INFO') as logs:
            self.restore(stash_id)
        text = '\n'.join(logs.output)
        self.assertIn('action=member_restore', text)
        self.assertIn('action=restore entity=member', text)
        self.assertNotIn(PHONE, text)


class RestoreDegradesSafelyTests(RestoreSetup):
    def test_an_account_that_left_the_family_is_not_relinked(self):
        stash_id = self.delete_ana()
        TreeMember.objects.filter(tree=self.tree, user=self.ana_user).delete()
        res = self.restore(stash_id)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['account_link'], 'dropped')
        ana = FamilyMember.objects.get(id=self.ana_id)
        self.assertIsNone(ana.user_id)
        self.assertEqual(ana.phone, PHONE)  # the rest is still exact

    def test_an_account_already_on_another_card_is_not_linked_twice(self):
        stash_id = self.delete_ana()
        FamilyMember.objects.create(tree=self.tree, first_name='Ana2', user=self.ana_user, created_by=self.owner)
        self.assertEqual(self.restore(stash_id).json()['account_link'], 'dropped')

    def test_a_link_to_someone_since_deleted_is_skipped_and_reported(self):
        stash_id = self.delete_ana()
        self.assertEqual(self.c.delete(f'{self.base}/members/{self.ugo.id}/').status_code, 200)  # Ugo has no links now
        res = self.restore(stash_id)
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body['restored_relationships'], 1)
        self.assertEqual([s['link'] for s in body['skipped_relationships']], ['Ana Rao is the Wife of Ugo Rao'])
        self.assertIn('no longer in this family', body['skipped_relationships'][0]['reason'])
        self.assertEqual(Relationship.objects.filter(tree=self.tree).count(), 1)
        self.assertTrue(EditHistory.objects.filter(change_description__startswith='Staff edit: Could not restore').exists())

    def test_a_link_the_rules_now_refuse_is_skipped_not_forced(self):
        stash_id = self.delete_ana()
        real = __import__('family_members.restore', fromlist=['x']).check_relationship
        calls = []

        def refuse_first(*a, **k):
            calls.append(1)
            return 'would create a loop' if len(calls) == 1 else real(*a, **k)

        with mock.patch('family_members.restore.check_relationship', side_effect=refuse_first):
            body = self.restore(stash_id).json()
        self.assertEqual((body['restored_relationships'], len(body['skipped_relationships'])), (1, 1))
        self.assertEqual(body['skipped_relationships'][0]['reason'], 'would create a loop')

    def test_if_the_old_id_has_been_taken_the_person_gets_a_new_one_with_everything_else(self):
        stash_id = self.delete_ana()
        FamilyMember.objects.create(id=self.ana_id, tree=self.tree, first_name='Squatter', created_by=self.owner)
        res = self.restore(stash_id)
        self.assertEqual(res.status_code, 200)
        new_id = res.json()['member']['id']
        self.assertNotEqual(new_id, self.ana_id)
        self.assertEqual(FamilyMember.objects.get(id=new_id).phone, PHONE)
        self.assertEqual(Relationship.objects.filter(member_1_id=new_id).count(), 2)

    def test_a_failure_part_way_restores_nothing_and_keeps_the_stash(self):
        stash_id = self.delete_ana()
        with mock.patch('family_members.restore.log_edit', side_effect=RuntimeError('disk full')):
            with self.assertRaises(RuntimeError):
                self.restore(stash_id)
        self.assertFalse(FamilyMember.objects.filter(id=self.ana_id).exists())
        self.assertTrue(StaffDeletedMember.objects.filter(id=stash_id).exists())  # can be retried

    def test_a_deleted_family_cannot_be_restored_into(self):
        stash_id = self.delete_ana()
        FamilyTree.objects.filter(id=self.tree.id).update(is_active=False)
        self.assertEqual(self.restore(stash_id).status_code, 409)
        self.assertTrue(StaffDeletedMember.objects.filter(id=stash_id).exists())
        self.assertFalse(FamilyMember.objects.filter(id=self.ana_id).exists())

    def test_a_stash_cannot_be_restored_through_another_trees_url(self):
        stash_id = self.delete_ana()
        other = make_tree(make_user('other'), 'Jones')
        res = self.c.post(f'/api/staff/trees/{other.id}/restores/{stash_id}/', {}, format='json')
        self.assertEqual(res.status_code, 404)
        self.assertFalse(FamilyMember.objects.filter(tree=other).exists())
        self.assertTrue(StaffDeletedMember.objects.filter(id=stash_id).exists())
        self.assertEqual(self.restore(99999).status_code, 404)


class RestoreIsStaffOnlyTests(RestoreSetup):
    def test_nobody_but_a_superuser_can_list_or_restore(self):
        stash_id = self.delete_ana()
        limited = make_user('limited')
        limited.is_staff = True
        limited.save()
        who = [('anonymous', APIClient(), (401,)), ('stranger', client_for(make_user('stranger')), (403,)),
               ('member', client_for(self.member), (403,)), ('the owner', client_for(self.owner), (403,)),
               ('the person themself', client_for(self.ana_user), (403,)), ('is_staff only', client_for(limited), (403,))]
        for label, client, codes in who:
            with self.subTest(who=label):
                self.assertIn(client.get(f'{self.base}/restores/').status_code, codes)
                self.assertIn(self.restore(stash_id, client).status_code, codes)
        self.assertFalse(FamilyMember.objects.filter(id=self.ana_id).exists())
        self.assertTrue(StaffDeletedMember.objects.filter(id=stash_id).exists())

    def test_the_methods_are_limited(self):
        stash_id = self.delete_ana()
        for method in ('post', 'put', 'patch', 'delete'):
            self.assertEqual(getattr(self.c, method)(f'{self.base}/restores/').status_code, 405, method)
        for method in ('get', 'put', 'patch', 'delete'):
            self.assertEqual(getattr(self.c, method)(f'{self.base}/restores/{stash_id}/').status_code, 405, method)

    def test_nothing_the_owner_or_members_can_reach_ever_shows_the_stashed_data(self):
        self.delete_ana()
        t = self.tree.id
        urls = [f'/api/family-members/?tree_id={t}', f'/api/relationships/?tree_id={t}', f'/api/edit-history/?tree_id={t}',
                '/api/family-trees/', f'/api/family-trees/{t}/', f'/api/join-requests/?tree_id={t}', '/api/users/me/']
        for who, client in (('owner', client_for(self.owner)), ('member', client_for(self.member)),
                            ('the person', client_for(self.ana_user))):
            for url in urls:
                res = client.get(url)
                with self.subTest(who=who, url=url):
                    self.assertNotIn(PHONE, res.content.decode())
                    self.assertNotIn('staff_deleted', res.content.decode())
        # ...and not even on the staff pages: the tree detail and the restore list carry no person data.
        for url in (f'/api/staff/trees/{t}/', f'{self.base}/restores/'):
            self.assertNotIn(PHONE, self.c.get(url).content.decode())

    def test_the_list_shows_names_and_dates_only(self):
        self.delete_ana()
        (item,) = self.c.get(f'{self.base}/restores/').json()
        self.assertEqual(set(item), {'id', 'name', 'deleted_at', 'expires_at', 'deleted_by', 'relationship_count'})
        self.assertEqual((item['name'], item['relationship_count'], item['deleted_by']), ('Ana Rao', 2, self.root.email))

    def test_the_stash_has_no_admin_page(self):
        self.assertNotIn(StaffDeletedMember, admin.site._registry)

    def test_every_staff_route_still_requires_a_superuser(self):
        from django.urls import get_resolver
        from family_trees.staff import IsSuperuser
        from family_trees.test_staff_write import all_patterns
        routes = [p for p in all_patterns(get_resolver().url_patterns) if str(p.pattern).startswith('staff/')]
        self.assertGreaterEqual(len([r for r in routes if 'restores' in str(r.pattern)]), 2)
        for p in routes:
            self.assertIn(IsSuperuser, p.callback.view_class.permission_classes, str(p.pattern))


class ExpiryAndCleanupTests(RestoreSetup):
    def test_an_expired_stash_cannot_be_restored_and_is_purged(self):
        stash_id = self.delete_ana()
        self.expire(stash_id)
        res = self.restore(stash_id)
        self.assertEqual(res.status_code, 410)
        self.assertIn('too long ago', res.json()['error'])
        self.assertFalse(StaffDeletedMember.objects.filter(id=stash_id).exists())
        self.assertFalse(FamilyMember.objects.filter(id=self.ana_id).exists())

    def test_expired_stashes_are_not_listed(self):
        stash_id = self.delete_ana()
        self.assertEqual(len(self.c.get(f'{self.base}/restores/').json()), 1)
        self.expire(stash_id)
        self.assertEqual(self.c.get(f'{self.base}/restores/').json(), [])

    def test_the_purge_command_removes_only_expired_stashes(self):
        old = self.delete_ana()
        fresh_member = FamilyMember.objects.create(tree=self.tree, first_name='Zed', created_by=self.owner)
        fresh = self.c.delete(f'{self.base}/members/{fresh_member.id}/').json()['restore_id']
        self.expire(old)
        out = StringIO()
        call_command('purge_staff_restores', stdout=out)
        self.assertIn('Purged 1 expired staff-restore stash.', out.getvalue())
        self.assertEqual(list(StaffDeletedMember.objects.values_list('id', flat=True)), [fresh])
        out = StringIO()
        call_command('purge_staff_restores', stdout=out)
        self.assertIn('Purged 0 expired staff-restore stashes.', out.getvalue())

    def test_a_new_staff_delete_purges_expired_stashes_on_the_way(self):
        old = self.delete_ana()
        self.expire(old)
        extra = FamilyMember.objects.create(tree=self.tree, first_name='Zed', created_by=self.owner)
        self.c.delete(f'{self.base}/members/{extra.id}/')
        self.assertFalse(StaffDeletedMember.objects.filter(id=old).exists())
        self.assertEqual(StaffDeletedMember.objects.count(), 1)

    def test_restoring_one_person_purges_other_expired_stashes_too(self):
        old = self.delete_ana()
        extra = FamilyMember.objects.create(tree=self.tree, first_name='Zed', created_by=self.owner)
        keep = self.c.delete(f'{self.base}/members/{extra.id}/').json()['restore_id']
        self.expire(old)
        self.assertEqual(self.restore(keep).status_code, 200)
        self.assertEqual(StaffDeletedMember.objects.count(), 0)

    def test_deleting_a_family_for_good_takes_its_stashes_with_it(self):
        self.delete_ana()
        self.tree.delete()
        self.assertEqual(StaffDeletedMember.objects.count(), 0)

    def test_a_stash_just_inside_the_window_still_restores(self):
        stash_id = self.delete_ana()
        StaffDeletedMember.objects.filter(id=stash_id).update(expires_at=timezone.now() + timedelta(seconds=30))
        self.assertEqual(self.restore(stash_id).status_code, 200)
