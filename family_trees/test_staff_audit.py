"""
What a superuser's edits leave behind: the history the tree's owner sees, and the server log.

The agreed requirement: every change made through staff edit mode is visibly labelled as staff in the
owner's edit history, with enough detail to tell what changed, and a delete records what went with it.
"""
import json
from unittest import mock

from django.test import TestCase

from config.testing import client_for, join, make_tree, make_user
from edit_history.models import EditHistory
from family_members.models import FamilyMember
from family_trees.test_staff import make_super
from relationships.models import Relationship, RelationshipType


class AuditSetup(TestCase):
    def setUp(self):
        self.owner = make_user('owner')
        self.member = make_user('member')
        self.tree = make_tree(self.owner, 'Smith Family')
        join(self.tree, self.member)
        mk = lambda n, **kw: FamilyMember.objects.create(tree=self.tree, first_name=n, last_name='Rao', created_by=self.owner, **kw)
        self.ann = mk('Ann', phone='555-1111', phone_public=False, birth_place='Pune')
        self.ben, self.cy = mk('Ben'), mk('Cy')
        self.brother = RelationshipType.objects.create(type_name='Brother', category='biological')
        self.father = RelationshipType.objects.create(type_name='Father', category='biological')
        self.rel = Relationship.objects.create(
            tree=self.tree, member_1=self.ann, member_2=self.ben, relationship_type=self.brother)
        self.root = make_super()
        self.c = client_for(self.root)
        self.base = f'/api/staff/trees/{self.tree.id}'

    def rows(self, **filters):
        return list(EditHistory.objects.filter(tree=self.tree, **filters).order_by('id'))


class StaffLabelTests(AuditSetup):
    def test_every_staff_write_is_flagged_labelled_and_attributed(self):
        b = self.base
        self.c.post(f'{b}/members/', {'first_name': 'Di', 'last_name': 'Rao'}, format='json')
        self.c.patch(f'{b}/members/{self.cy.id}/', {'first_name': 'Cyrus'}, format='json')
        self.c.post(f'{b}/relationships/', {'member_1': self.cy.id, 'member_2': self.ann.id,
                                            'relationship_type': self.father.id}, format='json')
        self.c.patch(f'{b}/relationships/{self.rel.id}/', {'relationship_type': self.father.id}, format='json')
        self.c.delete(f'{b}/relationships/{self.rel.id}/')
        self.c.delete(f'{b}/members/{self.ben.id}/')
        rows = self.rows()
        self.assertGreaterEqual(len(rows), 6)
        for r in rows:
            with self.subTest(row=r.change_description):
                self.assertTrue(r.by_staff)
                self.assertTrue(r.change_description.startswith('Staff edit: '))
                self.assertEqual(r.edited_by_id, self.root.id)

    def test_the_owner_sees_the_label_through_the_real_history_endpoint(self):
        self.c.patch(f'{self.base}/members/{self.cy.id}/', {'first_name': 'Cyrus'}, format='json')
        res = client_for(self.owner).get(f'/api/edit-history/?tree_id={self.tree.id}')
        self.assertEqual(res.status_code, 200)
        entry = res.json()[0]
        self.assertIs(entry['by_staff'], True)
        self.assertTrue(entry['change_description'].startswith('Staff edit: '))
        self.assertEqual(entry['edited_by']['email'], self.root.email)
        # ordinary members see it too: it is the tree's history, not a private owner view
        res = client_for(self.member).get(f'/api/edit-history/?tree_id={self.tree.id}')
        self.assertIs(res.json()[0]['by_staff'], True)

    def test_normal_edits_are_never_labelled_staff(self):
        owner = client_for(self.owner)
        owner.post('/api/family-members/', {'tree': self.tree.id, 'first_name': 'Di'}, format='json')
        owner.patch(f'/api/family-members/{self.cy.id}/', {'first_name': 'Cyrus'}, format='json')
        owner.delete(f'/api/relationships/{self.rel.id}/')
        rows = self.rows()
        self.assertEqual(len(rows), 3)
        self.assertFalse(any(r.by_staff or r.change_description.startswith('Staff edit') for r in rows))

    def test_a_superuser_acting_as_an_ordinary_member_is_recorded_as_one(self):
        # Staff edit mode is the only thing that produces the label; the normal endpoints never do,
        # whoever calls them.
        join(self.tree, self.root)
        self.c.post('/api/family-members/', {'tree': self.tree.id, 'first_name': 'Di'}, format='json')
        (row,) = self.rows()
        self.assertFalse(row.by_staff)

    def test_a_request_cannot_set_or_clear_the_flag(self):
        # Staff endpoint: always staff, whatever the body says.
        self.c.post(f'{self.base}/members/', {'first_name': 'Di', 'by_staff': False}, format='json')
        # Normal endpoint: never staff, whatever the body says.
        client_for(self.owner).post('/api/family-members/', {'tree': self.tree.id, 'first_name': 'Ed', 'by_staff': True},
                                    format='json')
        di, ed = self.rows()
        self.assertEqual((di.by_staff, ed.by_staff), (True, False))

    def test_the_history_list_shape_is_otherwise_unchanged(self):
        self.c.patch(f'{self.base}/members/{self.cy.id}/', {'first_name': 'Cyrus'}, format='json')
        entry = client_for(self.owner).get(f'/api/edit-history/?tree_id={self.tree.id}').json()[0]
        self.assertEqual(set(entry), {
            'id', 'entity_type', 'entity_id', 'field_name', 'old_value', 'new_value',
            'change_description', 'edited_by', 'edited_at', 'by_staff'})


class StaffFieldLevelDetailTests(AuditSetup):
    def test_a_person_edit_records_each_changed_field_with_old_and_new(self):
        self.c.patch(f'{self.base}/members/{self.ann.id}/',
                     {'first_name': 'Anna', 'birth_place': 'Delhi', 'last_name': 'Rao'}, format='json')
        rows = self.rows(entity_type='family_member')
        self.assertEqual([(r.field_name, r.old_value, r.new_value) for r in rows],
                         [('first_name', 'Ann', 'Anna'), ('birth_place', 'Pune', 'Delhi')])  # last_name unchanged: no row
        self.assertEqual(rows[0].change_description, 'Staff edit: Changed first name of Ann Rao')
        self.assertTrue(all(r.entity_id == self.ann.id for r in rows))

    def test_saving_without_changes_is_still_recorded(self):
        self.c.patch(f'{self.base}/members/{self.ann.id}/', {'first_name': 'Ann'}, format='json')
        (row,) = self.rows()
        self.assertEqual(row.change_description, 'Staff edit: Saved Ann Rao with no changes')

    def test_creating_a_person_stores_their_details(self):
        self.c.post(f'{self.base}/members/',
                    {'first_name': 'Di', 'last_name': 'Rao', 'gender': 'female', 'birth_place': 'Goa'}, format='json')
        (row,) = self.rows()
        details = json.loads(row.new_value)
        self.assertEqual((details['first_name'], details['gender'], details['birth_place']), ('Di', 'female', 'Goa'))

    def test_a_relationship_change_names_who_and_what_changed(self):
        self.c.patch(f'{self.base}/relationships/{self.rel.id}/',
                     {'relationship_type': self.father.id, 'member_2': self.cy.id}, format='json')
        rows = self.rows(entity_type='relationship')
        self.assertEqual({r.field_name: (r.old_value, r.new_value) for r in rows}, {
            'member_2': (f'Ben Rao (#{self.ben.id})', f'Cy Rao (#{self.cy.id})'),
            'relationship_type': ('Brother', 'Father'),
        })
        self.assertTrue(all(r.by_staff for r in rows))

    def test_creating_and_removing_a_relationship_store_a_snapshot(self):
        res = self.c.post(f'{self.base}/relationships/', {
            'member_1': self.cy.id, 'member_2': self.ann.id, 'relationship_type': self.father.id}, format='json')
        created = json.loads(self.rows()[0].new_value)
        self.assertEqual((created['id'], created['type'], created['reads']),
                         (res.json()['id'], 'Father', 'Cy Rao is the Father of Ann Rao'))
        self.c.delete(f'{self.base}/relationships/{self.rel.id}/')
        removed = json.loads(self.rows()[-1].old_value)
        self.assertEqual((removed['id'], removed['reads']), (self.rel.id, 'Ann Rao is the Brother of Ben Rao'))


class StaffDeleteSnapshotTests(AuditSetup):
    def test_deleting_a_person_records_them_and_every_link_that_went_with_them(self):
        extra = Relationship.objects.create(
            tree=self.tree, member_1=self.cy, member_2=self.ann, relationship_type=self.brother)
        res = self.c.delete(f'{self.base}/members/{self.ann.id}/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(Relationship.objects.count(), 0)  # both links went with Ann
        person_row, *link_rows = self.rows()
        self.assertEqual(person_row.change_description, 'Staff edit: Deleted member: Ann Rao (and 2 relationships)')
        snap = json.loads(person_row.old_value)
        self.assertEqual(snap['member']['first_name'], 'Ann')
        self.assertEqual(snap['member']['birth_place'], 'Pune')
        self.assertEqual({r['id'] for r in snap['relationships']}, {self.rel.id, extra.id})
        self.assertEqual(len(link_rows), 2)
        for r in link_rows:
            self.assertEqual((r.entity_type, r.by_staff), ('relationship', True))
            self.assertIn('(with Ann Rao)', r.change_description)
            self.assertIn('"reads"', r.old_value)

    def test_deleting_a_person_with_no_links_says_so_plainly(self):
        self.c.delete(f'{self.base}/members/{self.cy.id}/')
        (row,) = self.rows()
        self.assertEqual(row.change_description, 'Staff edit: Deleted member: Cy Rao')
        self.assertEqual(json.loads(row.old_value)['relationships'], [])

    def test_a_refused_delete_records_nothing(self):
        Relationship.objects.create(tree=self.tree, member_1=self.cy, member_2=self.ann, relationship_type=self.father)
        before = EditHistory.objects.count()
        res = self.c.delete(f'{self.base}/members/{self.cy.id}/')  # Cy is Ann's father: has descendants
        self.assertEqual(res.status_code, 400)
        self.assertEqual(EditHistory.objects.count(), before)


class StaffAuditPrivacyTests(AuditSetup):
    def test_a_private_phone_number_never_appears_in_any_history_row_or_log_line(self):
        with self.assertLogs('kinship.staff', level='INFO') as logs:
            self.c.patch(f'{self.base}/members/{self.ann.id}/',
                         {'phone': '999-9999', 'phone_public': True, 'first_name': 'Anna'}, format='json')
            self.c.post(f'{self.base}/members/', {'first_name': 'Di', 'phone': '777-7777'}, format='json')
            self.c.delete(f'{self.base}/members/{self.ann.id}/')
        everything = ' '.join(
            f'{r.change_description} {r.field_name} {r.old_value} {r.new_value}' for r in EditHistory.objects.all()
        ) + ' '.join(logs.output)
        for secret in ('555-1111', '999-9999', '777-7777'):
            self.assertNotIn(secret, everything)
        self.assertNotIn('"phone', everything)

    def test_the_server_log_names_the_fields_changed_but_not_their_values(self):
        with self.assertLogs('kinship.staff', level='INFO') as logs:
            self.c.patch(f'{self.base}/members/{self.cy.id}/', {'first_name': 'Zebediah', 'birth_place': 'Oslo'},
                         format='json')
        line = next(l for l in logs.output if 'staff_change' in l)
        self.assertIn(f'user={self.root.id} tree={self.tree.id} action=update entity=member id={self.cy.id}', line)
        self.assertIn('fields=first_name,birth_place', line)
        self.assertNotIn('Zebediah', line)
        self.assertNotIn('Oslo', line)


class StaffAuditAtomicityTests(AuditSetup):
    """No staff change without its record: if recording fails, the change is rolled back."""

    def test_a_failed_history_write_undoes_a_create(self):
        with mock.patch('family_members.services.log_edit', side_effect=RuntimeError('disk full')):
            with self.assertRaises(RuntimeError):
                self.c.post(f'{self.base}/members/', {'first_name': 'Di'}, format='json')
        self.assertFalse(FamilyMember.objects.filter(first_name='Di').exists())

    def test_a_failed_history_write_undoes_an_edit(self):
        with mock.patch('family_members.services.log_edit', side_effect=RuntimeError('disk full')):
            with self.assertRaises(RuntimeError):
                self.c.patch(f'{self.base}/members/{self.cy.id}/', {'first_name': 'Zed'}, format='json')
        self.cy.refresh_from_db()
        self.assertEqual(self.cy.first_name, 'Cy')

    def test_a_failed_history_write_undoes_a_delete_and_keeps_the_links(self):
        with mock.patch('family_members.services.log_edit', side_effect=RuntimeError('disk full')):
            with self.assertRaises(RuntimeError):
                self.c.delete(f'{self.base}/members/{self.ann.id}/')
        self.assertTrue(FamilyMember.objects.filter(id=self.ann.id).exists())
        self.assertTrue(Relationship.objects.filter(id=self.rel.id).exists())

    def test_a_failed_history_write_undoes_relationship_changes(self):
        with mock.patch('relationships.services.log_edit', side_effect=RuntimeError('disk full')):
            for call in (
                lambda: self.c.delete(f'{self.base}/relationships/{self.rel.id}/'),
                lambda: self.c.patch(f'{self.base}/relationships/{self.rel.id}/',
                                     {'relationship_type': self.father.id}, format='json'),
                lambda: self.c.post(f'{self.base}/relationships/', {
                    'member_1': self.cy.id, 'member_2': self.ann.id, 'relationship_type': self.father.id}, format='json'),
            ):
                with self.assertRaises(RuntimeError):
                    call()
        self.rel.refresh_from_db()
        self.assertEqual(self.rel.relationship_type, self.brother)
        self.assertEqual(Relationship.objects.count(), 1)
