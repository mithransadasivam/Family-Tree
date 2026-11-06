"""
The Django admin must not show a private phone number to staff, the same as the website's staff pages
(family_trees/staff.py serialises people with the superuser as viewer, so a private number comes back blank).
"""
from django.test import Client, TestCase

from config.testing import make_tree, make_user
from family_members.admin import PRIVATE_PHONE
from family_members.models import FamilyMember
from family_trees.test_staff import make_super

PRIVATE, PUBLIC = '555-0123', '555-0456'


class AdminPhoneTests(TestCase):
    def setUp(self):
        self.owner = make_user('owner')
        self.tree = make_tree(self.owner, 'Smith Family')
        mk = lambda n, **kw: FamilyMember.objects.create(tree=self.tree, first_name=n, last_name='Rao', created_by=self.owner, **kw)
        self.secret = mk('Ana', phone=PRIVATE, phone_public=False)
        self.open = mk('Ben', phone=PUBLIC, phone_public=True)
        self.root = make_super()
        self.client = Client()
        self.client.force_login(self.root)
        self.change = lambda m: f'/admin/family_members/familymember/{m.id}/change/'

    def page(self, url):
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200, url)
        return res.content.decode()

    def test_a_private_number_is_hidden_on_the_person_page(self):
        html = self.page(self.change(self.secret))
        self.assertNotIn(PRIVATE, html)
        self.assertIn(PRIVATE_PHONE, html)
        self.assertNotIn('name="phone"', html)  # not an editable (pre-filled) field either

    def test_a_public_number_is_still_shown(self):
        html = self.page(self.change(self.open))
        self.assertIn(PUBLIC, html)
        self.assertNotIn(PRIVATE_PHONE, html)

    def test_no_number_appears_in_the_list_or_other_admin_pages(self):
        for url in ('/admin/family_members/familymember/',
                    f'/admin/family_members/familymember/{self.secret.id}/delete/',
                    f'/admin/family_members/familymember/{self.secret.id}/history/',
                    '/admin/relationships/relationship/', '/admin/edit_history/edithistory/'):
            with self.subTest(url=url):
                self.assertNotIn(PRIVATE, self.page(url))

    def test_searching_the_list_by_a_private_number_finds_nobody(self):
        html = self.page(f'/admin/family_members/familymember/?q={PRIVATE}')
        self.assertNotIn('Ana', html.split('result_list')[-1])

    def test_the_owner_who_is_also_a_superuser_sees_their_own_trees_private_numbers(self):
        # Same rule as the website: the family's owner can see them. Only a superuser who is neither the
        # owner nor the person is kept out.
        self.owner.is_staff = self.owner.is_superuser = True
        self.owner.save()
        owner_client = Client()
        owner_client.force_login(self.owner)
        res = owner_client.get(self.change(self.secret))
        self.assertIn(PRIVATE, res.content.decode())

    def test_saving_a_person_in_the_admin_cannot_overwrite_or_reveal_the_number(self):
        data = {
            'tree': self.tree.id, 'created_by': self.owner.id, 'first_name': 'Anna', 'last_name': 'Rao', 'gender': 'female',
            'email': '', 'address': '', 'photo_url': '', 'birth_place': '',
            # a hostile or hopeful form: try to replace the number and flip it to public
            'phone': '000', 'phone_public': 'on',
        }
        res = self.client.post(self.change(self.secret), data)
        self.assertEqual(res.status_code, 302, res.content.decode()[:300])
        self.secret.refresh_from_db()
        self.assertEqual((self.secret.first_name, self.secret.phone, self.secret.phone_public), ('Anna', PRIVATE, False))

    def test_adding_a_person_in_the_admin_still_works(self):
        html = self.page('/admin/family_members/familymember/add/')
        self.assertNotIn('name="phone"', html)
        res = self.client.post('/admin/family_members/familymember/add/', {
            'tree': self.tree.id, 'created_by': self.owner.id, 'first_name': 'Cy', 'last_name': 'Rao', 'gender': '',
            'email': '', 'address': '', 'photo_url': '', 'birth_place': '',
        })
        self.assertEqual(res.status_code, 302)
        self.assertTrue(FamilyMember.objects.filter(first_name='Cy').exists())
