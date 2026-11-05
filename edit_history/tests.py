from django.contrib import admin
from django.test import Client, TestCase

from config.testing import make_tree, make_user
from edit_history.models import EditHistory
from edit_history.utils import log_edit
from family_trees.models import FamilyTree
from users.models import User

PASSWORD = 'correct-horse-battery-staple'


class EditHistoryAdminTests(TestCase):
    """The history is a record of what members did: staff can read it in the admin, nothing more.
    Admin changes are deliberately not written to it, and it cannot be altered from there."""

    def setUp(self):
        self.owner = make_user('owner')
        self.tree = make_tree(self.owner, 'History Tree')
        log_edit(self.tree, 'family_member', 1, self.owner, 'Added member: Ann Test')
        self.entry = EditHistory.objects.get()
        User.objects.create_superuser(email='boss@example.com', google_id='gb', password=PASSWORD)
        self.client = Client()
        assert self.client.login(email='boss@example.com', password=PASSWORD)
        self.base = '/admin/edit_history/edithistory/'

    def test_it_is_registered(self):
        self.assertTrue(admin.site.is_registered(EditHistory))

    def test_existing_history_is_visible_in_the_list_and_detail(self):
        res = self.client.get(self.base)
        self.assertContains(res, 'Added member: Ann Test')
        self.assertContains(res, 'History Tree')
        res = self.client.get(f'{self.base}{self.entry.pk}/change/')
        self.assertEqual(res.status_code, 200)  # opens read-only, as a "view" page
        self.assertContains(res, 'Added member: Ann Test')

    def test_the_detail_page_has_no_editable_fields_or_save_buttons(self):
        res = self.client.get(f'{self.base}{self.entry.pk}/change/')
        self.assertFalse(res.context['adminform'].form.fields)  # every field is read-only
        self.assertNotContains(res, 'name="_save"')
        self.assertNotContains(res, 'name="_continue"')
        self.assertNotContains(res, 'deletelink')

    def test_it_cannot_be_added_changed_or_deleted_even_by_a_superuser(self):
        self.assertEqual(self.client.get(self.base + 'add/').status_code, 403)
        res = self.client.post(f'{self.base}{self.entry.pk}/change/', {'change_description': 'tampered'})
        self.assertEqual(res.status_code, 403)
        self.assertEqual(self.client.get(f'{self.base}{self.entry.pk}/delete/').status_code, 403)
        self.assertEqual(self.client.post(f'{self.base}{self.entry.pk}/delete/', {'post': 'yes'}).status_code, 403)
        self.entry.refresh_from_db()
        self.assertEqual(self.entry.change_description, 'Added member: Ann Test')

    def test_the_bulk_delete_action_is_not_offered(self):
        res = self.client.get(self.base)
        self.assertNotContains(res, 'delete_selected')
        res = self.client.post(self.base, {'action': 'delete_selected', '_selected_action': [self.entry.pk],
                                           'post': 'yes'})
        self.assertTrue(EditHistory.objects.filter(pk=self.entry.pk).exists())
        self.assertNotEqual(res.status_code, 500)

    def test_admin_actions_do_not_add_history(self):
        before = EditHistory.objects.count()
        tree = FamilyTree.objects.get()
        self.client.post(f'/admin/family_trees/familytree/{tree.pk}/delete/', {'post': 'yes'})
        self.assertFalse(FamilyTree.objects.filter(pk=tree.pk).exists())
        # Only the history cascade-deleted with the tree changes; nothing new is written.
        self.assertLessEqual(EditHistory.objects.count(), before)
        self.assertFalse(EditHistory.objects.filter(change_description__icontains='admin').exists())
