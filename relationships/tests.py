from django.test import TestCase

from config.testing import client_for, join, make_tree, make_user
from family_members.models import FamilyMember
from relationships.models import Relationship, RelationshipType


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
