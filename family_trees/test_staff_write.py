"""
Superuser-only WRITE endpoints (/api/staff/trees/<id>/members|relationships/...).

The first half is the access matrix: every write endpoint x every kind of user who must NOT get
through, each asserted to be refused AND to have changed nothing. The second half is what a
superuser can do, and the integrity rules they still cannot get around.
"""
from django.conf import settings
from django.test import TestCase
from django.urls import URLPattern, URLResolver, get_resolver
from rest_framework.test import APIClient

from config.testing import client_for, join, make_tree, make_user
from edit_history.models import EditHistory
from family_members.models import FamilyMember
from family_trees.models import FamilyTree
from family_trees.staff import IsSuperuser
from family_trees.test_staff import make_super
from relationships.models import Relationship, RelationshipType
from users.views import get_tokens_for_user


def all_patterns(patterns=None):
    for p in patterns if patterns is not None else get_resolver().url_patterns:
        if isinstance(p, URLResolver):
            yield from all_patterns(p.url_patterns)
        elif isinstance(p, URLPattern):
            yield p


class StaffWriteSetup(TestCase):
    def setUp(self):
        self.owner = make_user('owner')
        self.member = make_user('member')
        self.outsider = make_user('outsider')
        self.tree = make_tree(self.owner, 'Smith Family')
        join(self.tree, self.member)
        mk = lambda n, **kw: FamilyMember.objects.create(tree=self.tree, first_name=n, created_by=self.owner, **kw)
        self.ann, self.ben, self.cy = mk('Ann', phone='555-1111', phone_public=False), mk('Ben'), mk('Cy')
        self.brother = RelationshipType.objects.create(type_name='Brother', category='biological')
        self.father = RelationshipType.objects.create(type_name='Father', category='biological')
        self.rel = Relationship.objects.create(
            tree=self.tree, member_1=self.ann, member_2=self.ben, relationship_type=self.brother)
        self.root = make_super()
        t = self.tree.id
        self.base = f'/api/staff/trees/{t}'

    def snapshot(self):
        return (
            list(FamilyMember.objects.order_by('id').values()),
            list(Relationship.objects.order_by('id').values()),
            EditHistory.objects.count(),
            list(FamilyTree.objects.order_by('id').values('id', 'is_active', 'owner_id')),
        )

    def history(self):
        return list(EditHistory.objects.filter(tree=self.tree).order_by('id').values_list('change_description', flat=True))


class StaffWriteAccessMatrixTests(StaffWriteSetup):
    def endpoints(self):
        """Every staff write operation, as (label, method, url, body)."""
        b = self.base
        return [
            ('member create', 'post', f'{b}/members/', {'first_name': 'Zed'}),
            ('member update', 'patch', f'{b}/members/{self.cy.id}/', {'first_name': 'Changed'}),
            ('member delete', 'delete', f'{b}/members/{self.cy.id}/', None),
            ('relationship create', 'post', f'{b}/relationships/', {
                'member_1': self.cy.id, 'member_2': self.ann.id, 'relationship_type': self.father.id}),
            ('relationship update', 'patch', f'{b}/relationships/{self.rel.id}/', {
                'relationship_type': self.father.id}),
            ('relationship delete', 'delete', f'{b}/relationships/{self.rel.id}/', None),
        ]

    def call(self, client, method, url, body):
        fn = getattr(client, method)
        return fn(url) if body is None else fn(url, body, format='json')

    def refused_for(self, label, client, codes):
        before = self.snapshot()
        for name, method, url, body in self.endpoints():
            with self.subTest(who=label, endpoint=name):
                res = self.call(client, method, url, body)
                self.assertIn(res.status_code, codes, res.content)
        self.assertEqual(self.snapshot(), before, f'{label} changed data')

    def test_anonymous(self):
        self.refused_for('anonymous', APIClient(), (401,))

    def test_a_signed_in_stranger(self):
        self.refused_for('outsider', client_for(self.outsider), (403,))

    def test_an_ordinary_tree_member(self):
        self.refused_for('member', client_for(self.member), (403,))

    def test_the_tree_owner_has_no_staff_powers_either(self):
        self.refused_for('owner', client_for(self.owner), (403,))

    def test_staff_flag_without_superuser(self):
        limited = make_user('limited')
        limited.is_staff = True
        limited.save()
        self.refused_for('is_staff only', client_for(limited), (403,))

    def test_a_deactivated_superuser(self):
        client = client_for(self.root)
        self.root.is_active = False
        self.root.save()
        self.refused_for('inactive superuser', client, (401, 403))

    def test_a_superuser_whose_flag_was_just_revoked(self):
        client = client_for(self.root)  # token minted while still a superuser
        self.root.is_superuser = False
        self.root.save()
        self.refused_for('revoked superuser', client, (403,))

    def test_a_user_cannot_promote_themselves_and_then_write(self):
        c = client_for(self.member)
        c.patch('/api/users/me/', {'is_superuser': True, 'is_staff': True}, format='json')
        self.refused_for('self-promoted member', c, (403,))

    def test_every_url_under_staff_requires_a_superuser(self):
        # Safety net for future endpoints: anything routed under staff/ must declare IsSuperuser,
        # so a new staff view cannot be added without the check.
        found = [p for p in all_patterns() if str(p.pattern).startswith('staff/')]
        self.assertGreaterEqual(len(found), 6)
        for p in found:
            view_class = p.callback.view_class
            with self.subTest(route=str(p.pattern)):
                self.assertIn(IsSuperuser, view_class.permission_classes)

    def test_the_staff_views_expose_only_the_methods_they_list(self):
        c = client_for(self.root)
        for url in (f'{self.base}/members/', f'{self.base}/relationships/'):
            for method in ('get', 'put', 'patch', 'delete'):
                self.assertEqual(getattr(c, method)(url).status_code, 405, (method, url))
        for url in (f'{self.base}/members/{self.cy.id}/', f'{self.base}/relationships/{self.rel.id}/'):
            for method in ('get', 'put', 'post'):
                self.assertEqual(getattr(c, method)(url).status_code, 405, (method, url))

    def test_a_cookie_session_from_a_foreign_origin_is_refused(self):
        token = get_tokens_for_user(self.root)['access']
        evil = APIClient()
        evil.cookies[settings.AUTH_COOKIE_ACCESS] = token
        res = evil.post(f'{self.base}/members/', {'first_name': 'Zed'}, format='json', HTTP_ORIGIN='https://evil.example')
        self.assertEqual(res.status_code, 403)
        self.assertFalse(FamilyMember.objects.filter(first_name='Zed').exists())
        ours = APIClient()
        ours.cookies[settings.AUTH_COOKIE_ACCESS] = token
        res = ours.post(f'{self.base}/members/', {'first_name': 'Zed'}, format='json', HTTP_ORIGIN='http://testserver')
        self.assertEqual(res.status_code, 201)


class NothingNormalWasLoosenedTests(StaffWriteSetup):
    """Being a superuser still gets you nothing on the normal endpoints, and H9 still binds everyone else."""

    def test_a_superuser_who_is_not_a_member_is_refused_on_every_normal_write(self):
        c = client_for(self.root)
        before = self.snapshot()
        res = [
            c.post('/api/family-members/', {'tree': self.tree.id, 'first_name': 'Zed'}, format='json'),
            c.patch(f'/api/family-members/{self.cy.id}/', {'first_name': 'X'}, format='json'),
            c.delete(f'/api/family-members/{self.cy.id}/'),
            c.post('/api/relationships/', {'tree': self.tree.id, 'member_1': self.cy.id, 'member_2': self.ann.id,
                                           'relationship_type': self.father.id}, format='json'),
            c.patch(f'/api/relationships/{self.rel.id}/', {'relationship_type': self.father.id}, format='json'),
            c.delete(f'/api/relationships/{self.rel.id}/'),
        ]
        self.assertEqual([r.status_code for r in res], [403] * 6)
        self.assertEqual(self.snapshot(), before)

    def test_a_non_owner_member_still_cannot_delete_on_the_normal_endpoints(self):  # H9
        c = client_for(self.member)
        self.assertEqual(c.delete(f'/api/family-members/{self.cy.id}/').status_code, 403)
        self.assertEqual(c.delete(f'/api/relationships/{self.rel.id}/').status_code, 403)
        self.assertTrue(FamilyMember.objects.filter(id=self.cy.id).exists())
        self.assertTrue(Relationship.objects.filter(id=self.rel.id).exists())

    def test_a_superuser_who_also_joined_the_tree_is_still_just_a_member_on_normal_endpoints(self):
        join(self.tree, self.root)
        c = client_for(self.root)
        self.assertEqual(c.delete(f'/api/family-members/{self.cy.id}/').status_code, 403)  # not the owner


class StaffWriteHappyPathTests(StaffWriteSetup):
    def setUp(self):
        super().setUp()
        self.c = client_for(self.root)  # a superuser who is NOT a member of this tree

    def test_add_edit_and_delete_a_person_in_a_tree_they_do_not_belong_to(self):
        res = self.c.post(f'{self.base}/members/', {'first_name': 'Di', 'last_name': 'Rao', 'gender': 'female'}, format='json')
        self.assertEqual(res.status_code, 201, res.content)
        di = FamilyMember.objects.get(id=res.json()['id'])
        self.assertEqual((di.tree_id, di.created_by_id), (self.tree.id, self.root.id))

        res = self.c.patch(f'{self.base}/members/{di.id}/', {'first_name': 'Dee'}, format='json')
        self.assertEqual((res.status_code, res.json()['first_name']), (200, 'Dee'))

        res = self.c.delete(f'{self.base}/members/{di.id}/')
        self.assertEqual(res.status_code, 200)
        self.assertFalse(FamilyMember.objects.filter(id=di.id).exists())
        self.assertEqual(self.history(), [
            'Staff edit: Added member: Di Rao',
            'Staff edit: Changed first name of Di Rao',
            'Staff edit: Deleted member: Dee Rao',
        ])

    def test_add_edit_and_delete_a_relationship(self):
        res = self.c.post(f'{self.base}/relationships/', {
            'member_1': self.cy.id, 'member_2': self.ann.id, 'relationship_type': self.father.id}, format='json')
        self.assertEqual(res.status_code, 201, res.content)
        rel = Relationship.objects.get(id=res.json()['id'])
        self.assertEqual((rel.tree_id, rel.created_by_id), (self.tree.id, self.root.id))

        res = self.c.patch(f'{self.base}/relationships/{rel.id}/', {'relationship_type': self.brother.id}, format='json')
        self.assertEqual((res.status_code, res.json()['relationship_type_name']), (200, 'Brother'))

        self.assertEqual(self.c.delete(f'{self.base}/relationships/{rel.id}/').status_code, 200)
        self.assertFalse(Relationship.objects.filter(id=rel.id).exists())
        self.assertEqual(self.history(), [
            'Staff edit: Added relationship: Cy is the Father of Ann',
            'Staff edit: Changed type of a relationship: Cy is the Brother of Ann',
            'Staff edit: Removed relationship: Cy is the Brother of Ann',
        ])

    def test_superuser_overrides_the_owner_only_delete_rule(self):  # H9 for everyone else is unchanged
        self.assertEqual(self.c.delete(f'{self.base}/relationships/{self.rel.id}/').status_code, 200)
        self.assertEqual(self.c.delete(f'{self.base}/members/{self.cy.id}/').status_code, 200)

    def test_the_tree_in_the_body_cannot_redirect_a_write(self):
        other = make_tree(make_user('other'), 'Jones')
        res = self.c.post(f'{self.base}/members/', {'tree': other.id, 'first_name': 'Zed'}, format='json')
        self.assertEqual(res.status_code, 400)
        res = self.c.post(f'{self.base}/members/', {'tree': self.tree.id, 'first_name': 'Zed'}, format='json')
        self.assertEqual(res.status_code, 201)
        self.assertFalse(FamilyMember.objects.filter(tree=other).exists())

    def test_a_person_cannot_be_moved_to_another_tree(self):
        other = make_tree(make_user('other'), 'Jones')
        res = self.c.patch(f'{self.base}/members/{self.cy.id}/', {'tree': other.id}, format='json')
        self.assertEqual(res.status_code, 400)
        self.cy.refresh_from_db()
        self.assertEqual(self.cy.tree_id, self.tree.id)

    def test_a_url_for_one_tree_cannot_reach_another_trees_people_or_links(self):
        other_owner = make_user('other')
        other = make_tree(other_owner, 'Jones')
        x = FamilyMember.objects.create(tree=other, first_name='Xan', created_by=other_owner)
        y = FamilyMember.objects.create(tree=other, first_name='Yu', created_by=other_owner)
        link = Relationship.objects.create(tree=other, member_1=x, member_2=y, relationship_type=self.brother)
        before = self.snapshot()
        for method, url, body in (
            ('patch', f'{self.base}/members/{x.id}/', {'first_name': 'Hacked'}),
            ('delete', f'{self.base}/members/{x.id}/', None),
            ('patch', f'{self.base}/relationships/{link.id}/', {'relationship_type': self.father.id}),
            ('delete', f'{self.base}/relationships/{link.id}/', None),
        ):
            res = getattr(self.c, method)(url) if body is None else getattr(self.c, method)(url, body, format='json')
            self.assertEqual(res.status_code, 404, (method, url))
        self.assertEqual(self.snapshot(), before)
        # ...and a link cannot join a person of this tree to a person of another.
        res = self.c.post(f'{self.base}/relationships/', {
            'member_1': self.cy.id, 'member_2': x.id, 'relationship_type': self.father.id}, format='json')
        self.assertEqual(res.status_code, 400)

    def test_unknown_tree_and_unknown_ids_are_404(self):
        self.assertEqual(self.c.post('/api/staff/trees/99999/members/', {'first_name': 'Z'}, format='json').status_code, 404)
        self.assertEqual(self.c.delete(f'{self.base}/members/99999/').status_code, 404)
        self.assertEqual(self.c.delete(f'{self.base}/relationships/99999/').status_code, 404)

    def test_a_body_that_is_not_an_object_is_a_400_not_a_crash(self):
        res = self.c.post(f'{self.base}/members/', [1, 2], format='json')
        self.assertEqual(res.status_code, 400)


class StaffWriteIntegrityRulesTests(StaffWriteSetup):
    """A superuser overrides who may act, not the rules that keep a tree coherent."""

    def setUp(self):
        super().setUp()
        self.c = client_for(self.root)

    def test_a_deleted_tree_refuses_every_write_with_409(self):
        self.tree.is_active = False
        self.tree.save()
        before = self.snapshot()
        b = self.base
        res = [
            self.c.post(f'{b}/members/', {'first_name': 'Z'}, format='json'),
            self.c.patch(f'{b}/members/{self.cy.id}/', {'first_name': 'Z'}, format='json'),
            self.c.delete(f'{b}/members/{self.cy.id}/'),
            self.c.post(f'{b}/relationships/', {'member_1': self.cy.id, 'member_2': self.ann.id,
                                                'relationship_type': self.father.id}, format='json'),
            self.c.patch(f'{b}/relationships/{self.rel.id}/', {'relationship_type': self.father.id}, format='json'),
            self.c.delete(f'{b}/relationships/{self.rel.id}/'),
        ]
        self.assertEqual([r.status_code for r in res], [409] * 6)
        self.assertEqual(self.snapshot(), before)
        # Viewing a deleted tree stays possible (read-only staff view).
        self.assertEqual(self.c.get(f'/api/staff/trees/{self.tree.id}/').status_code, 200)

    def test_a_parent_with_children_cannot_be_deleted(self):
        Relationship.objects.create(tree=self.tree, member_1=self.cy, member_2=self.ann, relationship_type=self.father)
        res = self.c.delete(f'{self.base}/members/{self.cy.id}/')
        self.assertEqual(res.status_code, 400)
        self.assertIn('has children', res.json()['error'])
        self.assertTrue(FamilyMember.objects.filter(id=self.cy.id).exists())

    def test_one_link_per_pair(self):
        res = self.c.post(f'{self.base}/relationships/', {
            'member_1': self.ben.id, 'member_2': self.ann.id, 'relationship_type': self.father.id}, format='json')
        self.assertEqual(res.status_code, 400)
        self.assertIn('already connected', res.json()['error'])

    def test_parent_loops_are_refused(self):
        Relationship.objects.create(tree=self.tree, member_1=self.cy, member_2=self.ann, relationship_type=self.father)
        res = self.c.post(f'{self.base}/relationships/', {
            'member_1': self.ann.id, 'member_2': self.cy.id, 'relationship_type': self.father.id}, format='json')
        self.assertEqual(res.status_code, 400)

    def test_a_private_phone_stays_private_and_unwritable_for_staff(self):
        res = self.c.patch(f'{self.base}/members/{self.ann.id}/',
                           {'phone': '000', 'phone_public': True, 'first_name': 'Anna'}, format='json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['phone'], '')
        self.ann.refresh_from_db()
        self.assertEqual((self.ann.phone, self.ann.phone_public, self.ann.first_name), ('555-1111', False, 'Anna'))

    def test_staff_cannot_link_a_person_to_an_account(self):
        # Account linking is the owner's call and is left out of staff edit mode.
        res = self.c.patch(f'{self.base}/members/{self.cy.id}/', {'user': self.member.id}, format='json')
        self.assertEqual(res.status_code, 400)
        res = self.c.post(f'{self.base}/members/', {'first_name': 'Zed', 'user': self.member.id}, format='json')
        self.assertEqual(res.status_code, 201)
        self.assertIsNone(FamilyMember.objects.get(first_name='Zed').user_id)
        self.cy.refresh_from_db()
        self.assertIsNone(self.cy.user_id)

    def test_every_write_leaves_a_trace_in_the_staff_log(self):
        with self.assertLogs('kinship.staff', level='INFO') as logs:
            self.c.post(f'{self.base}/members/', {'first_name': 'Zed'}, format='json')
            self.c.delete(f'{self.base}/relationships/{self.rel.id}/')
        text = '\n'.join(logs.output)
        self.assertIn(f'staff_write user={self.root.id} action=member_create tree={self.tree.id}', text)
        self.assertIn('action=relationship_delete', text)
