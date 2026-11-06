"""
The shared write functions (relationships/services.py, family_members/services.py), tested directly.
Both the normal views and the staff views go through them, so what they guarantee is tested once here.
"""
from django.test import TestCase

from config.testing import client_for, make_tree, make_user
from edit_history.models import EditHistory
from family_members import services as member_services
from family_members.models import FamilyMember
from relationships import services
from relationships.models import Relationship, RelationshipType
from utils.errors import ServiceError


class ServiceTestBase(TestCase):
    def setUp(self):
        self.owner = make_user('owner')
        self.tree = make_tree(self.owner)
        mk = lambda n: FamilyMember.objects.create(tree=self.tree, first_name=n, last_name='Rao', created_by=self.owner)
        self.ann, self.ben, self.cy = mk('Ann'), mk('Ben'), mk('Cy')
        self.father = RelationshipType.objects.create(type_name='Father', category='biological')
        self.brother = RelationshipType.objects.create(type_name='Brother', category='biological')

    def link(self, a, b, rtype=None):
        return Relationship.objects.create(
            tree=self.tree, member_1=a, member_2=b, relationship_type=rtype or self.father, created_by=self.owner)

    def history(self, entity_type):
        return list(EditHistory.objects.filter(tree=self.tree, entity_type=entity_type)
                    .order_by('id').values_list('change_description', flat=True))

    def deactivate(self):
        self.tree.is_active = False
        self.tree.save()


class RelationshipServiceTests(ServiceTestBase):
    def payload(self, a, b, rtype=None):
        return {'tree': self.tree.id, 'member_1': a.id, 'member_2': b.id,
                'relationship_type': (rtype or self.father).id}

    def test_create_records_who_what_and_history(self):
        rel = services.create_relationship(self.tree.id, self.payload(self.ann, self.ben), self.owner)
        self.assertEqual(rel.created_by, self.owner)
        self.assertEqual(self.history('relationship'), ['Added relationship: Ann Rao is the Father of Ben Rao'])

    def test_create_rejects_a_body_that_names_a_different_tree(self):
        other = make_tree(self.owner, 'Other')
        body = {**self.payload(self.ann, self.ben), 'tree': other.id}
        with self.assertRaises(ServiceError) as ctx:
            services.create_relationship(self.tree.id, body, self.owner)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertFalse(Relationship.objects.exists())

    def test_the_rules_still_apply(self):
        services.create_relationship(self.tree.id, self.payload(self.ann, self.ben), self.owner)
        with self.assertRaises(ServiceError) as ctx:  # the same pair the other way round
            services.create_relationship(self.tree.id, self.payload(self.ben, self.ann), self.owner)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertEqual(Relationship.objects.count(), 1)

    def test_update_logs_the_new_reading(self):
        rel = self.link(self.ann, self.ben)
        services.update_relationship(rel, {'relationship_type': self.brother.id}, self.owner)
        self.assertEqual(self.history('relationship'), ['Updated relationship: Ann Rao is the Brother of Ben Rao'])

    def test_delete_removes_the_link_and_is_now_logged(self):
        # Before this refactor a removed relationship left no trace in the history.
        rel = self.link(self.ann, self.ben)
        services.delete_relationship(rel, self.owner)
        self.assertFalse(Relationship.objects.filter(id=rel.id).exists())
        self.assertEqual(self.history('relationship'), ['Removed relationship: Ann Rao is the Father of Ben Rao'])

    def test_delete_of_a_link_that_just_vanished_is_a_404_not_a_crash(self):
        rel = self.link(self.ann, self.ben)
        stale = Relationship.objects.get(id=rel.id)
        rel.delete()
        with self.assertRaises(ServiceError) as ctx:
            services.delete_relationship(stale, self.owner)
        self.assertEqual(ctx.exception.status_code, 404)

    def test_a_deleted_tree_refuses_every_relationship_write(self):
        rel = self.link(self.ann, self.ben)
        self.deactivate()
        for call in (
            lambda: services.create_relationship(self.tree.id, self.payload(self.ann, self.cy), self.owner),
            lambda: services.update_relationship(rel, {'relationship_type': self.brother.id}, self.owner),
            lambda: services.delete_relationship(rel, self.owner),
        ):
            with self.assertRaises(ServiceError) as ctx:
                call()
            self.assertEqual(ctx.exception.status_code, 409)
        self.assertEqual(Relationship.objects.count(), 1)
        self.assertEqual(Relationship.objects.get().relationship_type, self.father)
        self.assertEqual(self.history('relationship'), [])


class MemberServiceTests(ServiceTestBase):
    def test_create_update_delete_are_logged(self):
        body = {'tree': self.tree.id, 'first_name': 'Di', 'last_name': 'Rao'}
        di = member_services.create_member(self.tree.id, body, self.owner)
        member_services.update_member(di, {'first_name': 'Dee'}, self.owner)
        member_services.delete_member(di, self.owner)
        self.assertEqual(self.history('family_member'),
                         ['Added member: Di Rao', 'Updated member: Di Rao', 'Deleted member: Dee Rao'])

    def test_create_rejects_a_body_that_names_a_different_tree(self):
        other = make_tree(self.owner, 'Other')
        with self.assertRaises(ServiceError):
            member_services.create_member(self.tree.id, {'tree': other.id, 'first_name': 'Di'}, self.owner)
        self.assertFalse(FamilyMember.objects.filter(first_name='Di').exists())

    def test_a_parent_with_children_cannot_be_deleted(self):
        self.link(self.ann, self.ben)
        with self.assertRaises(ServiceError) as ctx:
            member_services.delete_member(self.ann, self.owner)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertTrue(FamilyMember.objects.filter(id=self.ann.id).exists())

    def test_someone_who_cannot_see_a_private_phone_cannot_overwrite_it(self):
        self.ben.phone = '111'
        self.ben.save()
        stranger = make_user('stranger')
        member_services.update_member(self.ben, {'phone': '999', 'phone_public': True, 'first_name': 'Benji'}, stranger)
        self.ben.refresh_from_db()
        self.assertEqual((self.ben.phone, self.ben.phone_public, self.ben.first_name), ('111', False, 'Benji'))

    def test_a_deleted_tree_refuses_every_member_write(self):
        self.deactivate()
        for call in (
            lambda: member_services.create_member(self.tree.id, {'tree': self.tree.id, 'first_name': 'Di'}, self.owner),
            lambda: member_services.update_member(self.ann, {'first_name': 'X'}, self.owner),
            lambda: member_services.delete_member(self.cy, self.owner),
        ):
            with self.assertRaises(ServiceError) as ctx:
                call()
            self.assertEqual(ctx.exception.status_code, 409)
        self.ann.refresh_from_db()
        self.assertEqual(self.ann.first_name, 'Ann')
        self.assertTrue(FamilyMember.objects.filter(id=self.cy.id).exists())
        self.assertFalse(FamilyMember.objects.filter(first_name='Di').exists())
        self.assertEqual(self.history('family_member'), [])


class NormalEndpointsStillBehaveTests(ServiceTestBase):
    """Through the real URLs: the refactor changed no answers, and a removed link is now in the history."""

    def test_owner_delete_over_http_is_logged(self):
        rel = self.link(self.ann, self.ben)
        res = client_for(self.owner).delete(f'/api/relationships/{rel.id}/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json(), {'message': 'Relationship deleted'})
        self.assertEqual(self.history('relationship'), ['Removed relationship: Ann Rao is the Father of Ben Rao'])

    def test_validation_errors_keep_their_shape_and_status(self):
        res = client_for(self.owner).post('/api/relationships/', {'tree': self.tree.id}, format='json')
        self.assertEqual(res.status_code, 400)
        self.assertIn('member_1', res.json())

    def test_a_pair_already_connected_is_still_a_plain_400(self):
        self.link(self.ann, self.ben)
        res = client_for(self.owner).post('/api/relationships/', {
            'tree': self.tree.id, 'member_1': self.ben.id, 'member_2': self.ann.id,
            'relationship_type': self.brother.id}, format='json')
        self.assertEqual(res.status_code, 400)
        self.assertIn('already connected', res.json()['error'])
