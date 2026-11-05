import os
from io import StringIO
from pathlib import Path
from unittest import mock

from django.contrib import admin
from django.contrib.auth import authenticate
from django.core.management import CommandError, call_command
from django.test import Client, TestCase, override_settings

from communities.models import Community
from config.testing import make_tree, make_user
from family_codes.models import FamilyCode
from family_members.models import FamilyMember
from family_trees.models import FamilyTree, TreeMember
from join_requests.models import JoinRequest
from relationships.models import Relationship, RelationshipType
from users.models import User

BASE_DIR = Path(__file__).resolve().parent.parent
PASSWORD = 'correct-horse-battery-staple'


def staff_client(email='boss@example.com'):
    user = User.objects.create_superuser(email=email, google_id=f'g-{email}', password=PASSWORD)
    client = Client()
    assert client.login(email=email, password=PASSWORD)
    return user, client


class AdminAccessTests(TestCase):
    def test_ordinary_users_are_not_staff(self):
        u = make_user('plain')
        self.assertFalse(u.is_staff)
        self.assertFalse(u.is_superuser)
        self.assertFalse(u.has_perm('family_trees.delete_familytree'))

    def test_anonymous_visitors_are_sent_to_the_admin_login(self):
        res = Client().get('/admin/')
        self.assertEqual(res.status_code, 302)
        self.assertIn('/admin/login/', res['Location'])

    def test_a_signed_in_non_staff_user_cannot_use_the_admin(self):
        make_user('plain')
        u = User.objects.get(email='plain@example.com')
        u.set_password(PASSWORD)
        u.save()
        client = Client()
        self.assertTrue(client.login(email=u.email, password=PASSWORD))
        res = client.get('/admin/')
        self.assertEqual(res.status_code, 302)
        self.assertIn('/admin/login/', res['Location'])
        self.assertEqual(client.get('/admin/family_trees/familytree/').status_code, 302)

    def test_an_inactive_superuser_cannot_log_in(self):
        user, _ = staff_client('gone@example.com')
        user.is_active = False
        user.save()
        self.assertIsNone(authenticate(email=user.email, password=PASSWORD))

    def test_admin_login_form_accepts_email_and_password(self):
        user = User.objects.create_superuser(email='form@example.com', google_id='gf', password=PASSWORD)
        client = Client()
        res = client.post('/admin/login/', {'username': user.email, 'password': PASSWORD, 'next': '/admin/'})
        self.assertEqual(res.status_code, 302)
        self.assertEqual(client.get('/admin/').status_code, 200)

    @override_settings(ALLOWED_HOSTS=['kinship.example.com'])
    def test_admin_login_works_behind_the_https_proxy_with_csrf_checks_on(self):
        # Railway terminates TLS: Django sees http but X-Forwarded-Proto says https and the
        # browser's Origin is https. Without SECURE_PROXY_SSL_HEADER the CSRF check rejects it.
        User.objects.create_superuser(email='proxy@example.com', google_id='gp', password=PASSWORD)
        client = Client(enforce_csrf_checks=True)
        proxy = {'HTTP_X_FORWARDED_PROTO': 'https', 'HTTP_HOST': 'kinship.example.com'}
        page = client.get('/admin/login/', secure=False, **proxy)
        token = page.cookies['csrftoken'].value
        res = client.post(
            '/admin/login/',
            {'username': 'proxy@example.com', 'password': PASSWORD, 'next': '/admin/',
             'csrfmiddlewaretoken': token},
            HTTP_ORIGIN='https://kinship.example.com', **proxy,
        )
        self.assertEqual(res.status_code, 302, res.content[:300])

    def test_wrong_password_is_refused(self):
        User.objects.create_superuser(email='pw@example.com', google_id='gw', password=PASSWORD)
        res = Client().post('/admin/login/', {'username': 'pw@example.com', 'password': 'nope', 'next': '/admin/'})
        self.assertEqual(res.status_code, 200)  # form redisplayed with an error, no redirect


class AdminRegistrationTests(TestCase):
    MODELS = [FamilyTree, FamilyMember, Relationship, RelationshipType, TreeMember,
              JoinRequest, FamilyCode, User]

    def test_every_requested_model_is_registered(self):
        for model in self.MODELS:
            self.assertTrue(admin.site.is_registered(model), model.__name__)

    def test_superuser_can_open_every_list_and_add_page(self):
        _, client = staff_client()
        for model in self.MODELS:
            meta = model._meta
            base = f'/admin/{meta.app_label}/{meta.model_name}/'
            self.assertEqual(client.get(base).status_code, 200, base)
            self.assertEqual(client.get(base + 'add/').status_code, 200, base + 'add/')

    def build_data(self):
        owner, other = make_user('owner'), make_user('other')
        tree = make_tree(owner, 'Admin Tree')
        TreeMember.objects.create(tree=tree, user=other)
        a = FamilyMember.objects.create(tree=tree, first_name='A', created_by=owner)
        b = FamilyMember.objects.create(tree=tree, first_name='B', created_by=owner)
        rtype = RelationshipType.objects.create(type_name='Brother', category='biological')
        rel = Relationship.objects.create(tree=tree, member_1=a, member_2=b, relationship_type=rtype)
        code = FamilyCode.objects.create(tree=tree, code='ADMIN12345', created_by=owner)
        req = JoinRequest.objects.create(tree=tree, requester=other, family_code_used=code)
        return owner, tree, a, b, rel, code, req

    def test_superuser_sees_data_from_every_user_in_the_lists(self):
        owner, tree, *_ = self.build_data()
        _, client = staff_client()
        self.assertContains(client.get('/admin/family_trees/familytree/'), 'Admin Tree')
        self.assertContains(client.get('/admin/family_members/familymember/'), 'A ')
        self.assertContains(client.get('/admin/users/user/'), owner.email)
        self.assertContains(client.get('/admin/family_codes/familycode/'), 'ADMIN12345')

    def test_superuser_can_edit_a_person_that_belongs_to_someone_else(self):
        _, _, a, *_ = self.build_data()
        _, client = staff_client()
        url = f'/admin/family_members/familymember/{a.id}/change/'
        form = client.get(url).context['adminform'].form
        data = {name: ('' if value is None else value) for name, value in form.initial.items()}
        data.update(first_name='Renamed', tree=a.tree_id, gender='', phone_public='')
        res = client.post(url, {k: v for k, v in data.items() if v is not None})
        self.assertEqual(res.status_code, 302, getattr(res, 'context', None) and res.context['adminform'].form.errors)
        a.refresh_from_db()
        self.assertEqual(a.first_name, 'Renamed')

    def delete_via_admin(self, client, model, obj):
        meta = model._meta
        url = f'/admin/{meta.app_label}/{meta.model_name}/{obj.pk}/delete/'
        self.assertEqual(client.get(url).status_code, 200)  # the confirmation page
        res = client.post(url, {'post': 'yes'})
        self.assertEqual(res.status_code, 302)
        self.assertFalse(model.objects.filter(pk=obj.pk).exists())

    def test_superuser_can_delete_relationships_members_requests_codes_and_trees(self):
        owner, tree, a, b, rel, code, req = self.build_data()
        _, client = staff_client()
        self.delete_via_admin(client, Relationship, rel)
        self.delete_via_admin(client, JoinRequest, req)
        self.delete_via_admin(client, FamilyCode, code)
        self.delete_via_admin(client, FamilyMember, b)
        self.delete_via_admin(client, TreeMember, TreeMember.objects.get(tree=tree, role='owner'))
        self.delete_via_admin(client, FamilyTree, tree)
        self.assertTrue(FamilyMember.objects.filter(pk=a.pk).count() == 0)  # went with its tree

    def test_superuser_can_delete_a_user(self):
        victim = make_user('victim')
        _, client = staff_client()
        self.delete_via_admin(client, User, victim)

    def test_superuser_can_set_a_users_password_from_the_admin(self):
        victim = make_user('google_only')  # created like a Google sign-in: no usable password
        self.assertFalse(victim.has_usable_password())
        _, client = staff_client()
        url = f'/admin/users/user/{victim.pk}/password/'
        self.assertEqual(client.get(url).status_code, 200)
        res = client.post(url, {'password1': 'another-long-password-9', 'password2': 'another-long-password-9'})
        self.assertEqual(res.status_code, 302)
        victim.refresh_from_db()
        self.assertTrue(victim.check_password('another-long-password-9'))


class MakeAdminCommandTests(TestCase):
    def run_cmd(self, *args, **env):
        out = StringIO()
        with mock.patch.dict(os.environ, env):
            call_command('makeadmin', *args, stdout=out)
        return out.getvalue()

    def test_grants_staff_and_superuser_and_sets_the_password_from_an_env_var(self):
        user = make_user('mithran')
        bystander = make_user('bystander')
        self.assertFalse(user.has_usable_password())
        self.run_cmd('mithran@example.com', '--password-env', 'KINSHIP_PW', KINSHIP_PW=PASSWORD)
        user.refresh_from_db()
        self.assertTrue(user.is_staff and user.is_superuser and user.is_active)
        self.assertTrue(user.check_password(PASSWORD))
        self.assertIsNotNone(authenticate(email='mithran@example.com', password=PASSWORD))
        bystander.refresh_from_db()
        self.assertFalse(bystander.is_staff or bystander.is_superuser)

    def test_prompts_for_the_password_when_no_env_var_is_given(self):
        user = make_user('prompted')
        with mock.patch('users.management.commands.makeadmin.getpass.getpass', side_effect=[PASSWORD, PASSWORD]):
            self.run_cmd('prompted@example.com')
        user.refresh_from_db()
        self.assertTrue(user.check_password(PASSWORD))

    def test_mismatched_prompts_change_nothing(self):
        user = make_user('mismatch')
        with mock.patch('users.management.commands.makeadmin.getpass.getpass', side_effect=[PASSWORD, 'other']):
            with self.assertRaises(CommandError):
                self.run_cmd('mismatch@example.com')
        user.refresh_from_db()
        self.assertFalse(user.is_staff or user.is_superuser)

    def test_flags_only_keeps_the_existing_password_untouched(self):
        user = make_user('keep')
        user.set_password(PASSWORD)
        user.save()
        self.run_cmd('keep@example.com', '--no-password')
        user.refresh_from_db()
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.check_password(PASSWORD))

    def test_unknown_account_is_an_error_and_creates_nothing(self):
        with self.assertRaises(CommandError):
            self.run_cmd('nobody@example.com', '--no-password')
        self.assertFalse(User.objects.filter(email='nobody@example.com').exists())

    def test_weak_or_empty_passwords_are_refused(self):
        make_user('weak')
        with self.assertRaises(CommandError):
            self.run_cmd('weak@example.com', '--password-env', 'KINSHIP_PW', KINSHIP_PW='1234')
        with self.assertRaises(CommandError):
            self.run_cmd('weak@example.com', '--password-env', 'KINSHIP_PW_MISSING')
        self.assertFalse(User.objects.get(email='weak@example.com').is_superuser)


class NoPublicAdminLinkTests(TestCase):
    """/admin/ is reachable only by typing the address: nothing in the apps points at it."""

    SCAN = [('web/src', {'.ts', '.tsx', '.html'}), ('web/index.html', {'.html'}),
            ('webapp', {'.html', '.js'}), ('app/src/main', {'.kt', '.xml'}),
            ('README.md', {'.md'})]

    def test_no_client_or_page_links_to_the_admin(self):
        offenders = []
        for rel, exts in self.SCAN:
            root = BASE_DIR / rel
            files = [root] if root.is_file() else [p for p in root.rglob('*') if p.is_file()]
            for path in files:
                if path.suffix in exts:
                    text = path.read_text(encoding='utf-8', errors='ignore')
                    if '/admin' in text.replace('\\', '/'):
                        offenders.append(str(path.relative_to(BASE_DIR)))
        self.assertEqual(offenders, [])

    def test_the_admin_is_mounted_exactly_once_at_admin(self):
        from django.urls import resolve
        self.assertEqual(resolve('/admin/').app_name, 'admin')
        # The website's catch-all must not swallow it (nor hide a missing admin page as the SPA).
        self.assertEqual(Client().get('/admin/nope/').status_code, 302)
