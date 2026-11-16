from django.test import TestCase

from config.testing import client_for, join, make_tree, make_user
from family_members.models import FamilyMember
from relationships.models import Relationship, RelationshipType


class OwnerOnlyDeleteTests(TestCase):
    """
    H9 permission model: every tree member can ADD and EDIT people and relationships, but only the
    tree owner can DELETE a person or a relationship.
    """

    def setUp(self):
        self.owner = make_user('owner')
        self.member = make_user('member')
        self.outsider = make_user('outsider')
        self.tree = make_tree(self.owner)
        join(self.tree, self.member)
        mk = lambda n, by: FamilyMember.objects.create(tree=self.tree, first_name=n, created_by=by)
        self.a, self.b = mk('A', self.owner), mk('B', self.member)
        self.brother = RelationshipType.objects.create(type_name='Brother', category='biological')
        self.rel = Relationship.objects.create(
            tree=self.tree, member_1=self.a, member_2=self.b, relationship_type=self.brother,
            created_by=self.member)

    # -- deleting a person ------------------------------------------------------------------
    def test_non_owner_cannot_delete_a_person_even_one_they_created(self):
        res = client_for(self.member).delete(f'/api/family-members/{self.b.id}/')
        self.assertEqual(res.status_code, 403)
        self.assertIn('owner', res.json()['error'].lower())
        self.assertTrue(FamilyMember.objects.filter(id=self.b.id).exists())

    def test_owner_can_delete_a_person(self):
        res = client_for(self.owner).delete(f'/api/family-members/{self.b.id}/')
        self.assertEqual(res.status_code, 200)
        self.assertFalse(FamilyMember.objects.filter(id=self.b.id).exists())
        # Their relationships went with them.
        self.assertFalse(Relationship.objects.filter(id=self.rel.id).exists())

    def test_owner_still_cannot_delete_a_parent_with_children(self):
        father = RelationshipType.objects.create(type_name='Father', category='biological')
        Relationship.objects.filter(id=self.rel.id).delete()
        Relationship.objects.create(
            tree=self.tree, member_1=self.a, member_2=self.b, relationship_type=father)
        res = client_for(self.owner).delete(f'/api/family-members/{self.a.id}/')
        self.assertEqual(res.status_code, 400)
        self.assertTrue(FamilyMember.objects.filter(id=self.a.id).exists())

    def test_outsider_cannot_delete_a_person(self):
        res = client_for(self.outsider).delete(f'/api/family-members/{self.b.id}/')
        self.assertEqual(res.status_code, 403)
        self.assertTrue(FamilyMember.objects.filter(id=self.b.id).exists())

    # -- deleting a relationship ------------------------------------------------------------
    def test_non_owner_cannot_delete_a_relationship_even_one_they_created(self):
        res = client_for(self.member).delete(f'/api/relationships/{self.rel.id}/')
        self.assertEqual(res.status_code, 403)
        self.assertIn('owner', res.json()['error'].lower())
        self.assertTrue(Relationship.objects.filter(id=self.rel.id).exists())

    def test_owner_can_delete_a_relationship(self):
        res = client_for(self.owner).delete(f'/api/relationships/{self.rel.id}/')
        self.assertEqual(res.status_code, 200)
        self.assertFalse(Relationship.objects.filter(id=self.rel.id).exists())

    def test_outsider_cannot_delete_a_relationship(self):
        res = client_for(self.outsider).delete(f'/api/relationships/{self.rel.id}/')
        self.assertEqual(res.status_code, 403)
        self.assertTrue(Relationship.objects.filter(id=self.rel.id).exists())

    # -- add / edit stay open to every member -----------------------------------------------
    def test_every_member_can_add_and_edit_people(self):
        for user in (self.owner, self.member):
            c = client_for(user)
            res = c.post('/api/family-members/', {'tree': self.tree.id, 'first_name': f'By{user.id}'}, format='json')
            self.assertEqual(res.status_code, 201, res.content)
            res = c.patch(f'/api/family-members/{res.json()["id"]}/', {'last_name': 'Edited'}, format='json')
            self.assertEqual(res.status_code, 200, res.content)
        # ...including people somebody else created.
        res = client_for(self.member).patch(
            f'/api/family-members/{self.a.id}/', {'first_name': 'Alex'}, format='json')
        self.assertEqual(res.status_code, 200)
        self.a.refresh_from_db()
        self.assertEqual(self.a.first_name, 'Alex')

    def test_every_member_can_add_and_edit_relationships(self):
        sister = RelationshipType.objects.create(type_name='Sister', category='biological')
        for user in (self.owner, self.member):
            c = client_for(user)
            extra = FamilyMember.objects.create(tree=self.tree, first_name=f'X{user.id}', created_by=user)
            res = c.post('/api/relationships/', {
                'tree': self.tree.id, 'member_1': extra.id, 'member_2': self.a.id,
                'relationship_type': self.brother.id}, format='json')
            self.assertEqual(res.status_code, 201, res.content)
            res = c.patch(f'/api/relationships/{res.json()["id"]}/',
                          {'relationship_type': sister.id}, format='json')
            self.assertEqual(res.status_code, 200, res.content)
        # ...including a link somebody else created.
        res = client_for(self.member).patch(
            f'/api/relationships/{self.rel.id}/', {'relationship_type': sister.id}, format='json')
        self.assertEqual(res.status_code, 200)

    def test_non_owner_delete_is_rejected_for_inactive_tree_too(self):
        self.tree.is_active = False
        self.tree.save()
        self.assertEqual(client_for(self.member).delete(f'/api/family-members/{self.b.id}/').status_code, 403)
        self.assertTrue(FamilyMember.objects.filter(id=self.b.id).exists())


class PrivatePhoneBypassTests(TestCase):
    """C2: linking yourself to a person (`user`) must not unlock their private phone number."""

    def setUp(self):
        self.owner = make_user('owner')
        self.snoop = make_user('snoop')
        self.tree = make_tree(self.owner)
        join(self.tree, self.snoop)
        self.member = FamilyMember.objects.create(
            tree=self.tree, first_name='Gran', phone='555-9999', phone_public=False,
            created_by=self.owner)

    def test_member_cannot_link_themselves_to_read_a_private_phone(self):
        c = client_for(self.snoop)
        res = c.patch(f'/api/family-members/{self.member.id}/', {'user': self.snoop.id}, format='json')
        self.assertEqual(res.status_code, 400)
        self.member.refresh_from_db()
        self.assertIsNone(self.member.user_id)
        self.assertEqual(c.get(f'/api/family-members/{self.member.id}/').json()['phone'], '')

    def test_member_cannot_link_someone_else(self):
        res = client_for(self.snoop).patch(
            f'/api/family-members/{self.member.id}/', {'user': self.owner.id}, format='json')
        self.assertEqual(res.status_code, 400)

    def test_cannot_create_a_person_already_linked_to_oneself_to_read_the_phone(self):
        res = client_for(self.snoop).post('/api/family-members/', {
            'tree': self.tree.id, 'first_name': 'Fake', 'phone': '555-1', 'user': self.snoop.id,
        }, format='json')
        self.assertEqual(res.status_code, 201)
        created = FamilyMember.objects.get(id=res.json()['id'])
        self.assertIsNone(created.user_id)

    def test_owner_still_sees_private_phone(self):
        res = client_for(self.owner).get(f'/api/family-members/{self.member.id}/')
        self.assertEqual(res.json()['phone'], '555-9999')

    def test_unchanged_user_link_can_be_resent(self):
        self.member.user = self.owner
        self.member.save()
        res = client_for(self.owner).patch(
            f'/api/family-members/{self.member.id}/',
            {'user': self.owner.id, 'first_name': 'Gran2'}, format='json')
        self.assertEqual(res.status_code, 200)

    def test_only_the_owner_can_clear_or_set_the_link(self):
        self.member.user = self.owner
        self.member.save()
        url = f'/api/family-members/{self.member.id}/'
        self.assertEqual(client_for(self.snoop).patch(url, {'user': None}, format='json').status_code, 400)
        self.assertEqual(client_for(self.owner).patch(url, {'user': None}, format='json').status_code, 200)
        self.assertEqual(client_for(self.owner).patch(url, {'user': self.snoop.id}, format='json').status_code, 200)
        self.member.refresh_from_db()
        self.assertEqual(self.member.user_id, self.snoop.id)

    def test_owner_cannot_link_a_user_outside_the_tree(self):
        stranger = make_user('stranger')
        res = client_for(self.owner).patch(
            f'/api/family-members/{self.member.id}/', {'user': stranger.id}, format='json')
        self.assertEqual(res.status_code, 400)


class MemberTreeImmutableTests(TestCase):
    """C1: a member must never be movable into (or out of) another tree via PATCH."""

    def setUp(self):
        self.attacker = make_user('attacker')
        self.victim = make_user('victim')
        self.my_tree = make_tree(self.attacker, 'Mine')
        self.victim_tree = make_tree(self.victim, 'Victims')
        self.member = FamilyMember.objects.create(
            tree=self.my_tree, first_name='Pat', created_by=self.attacker)

    def test_cannot_move_member_into_someone_elses_tree(self):
        res = client_for(self.attacker).patch(
            f'/api/family-members/{self.member.id}/', {'tree': self.victim_tree.id}, format='json')
        self.assertEqual(res.status_code, 400)
        self.member.refresh_from_db()
        self.assertEqual(self.member.tree_id, self.my_tree.id)
        self.assertFalse(FamilyMember.objects.filter(tree=self.victim_tree).exists())

    def test_cannot_move_member_into_another_tree_even_if_also_a_member(self):
        other = make_tree(self.victim, 'Shared')
        join(other, self.attacker)
        res = client_for(self.attacker).patch(
            f'/api/family-members/{self.member.id}/', {'tree': other.id}, format='json')
        self.assertEqual(res.status_code, 400)
        self.member.refresh_from_db()
        self.assertEqual(self.member.tree_id, self.my_tree.id)

    def test_sending_the_same_tree_is_harmless(self):
        res = client_for(self.attacker).patch(
            f'/api/family-members/{self.member.id}/',
            {'tree': self.my_tree.id, 'first_name': 'Patricia'}, format='json')
        self.assertEqual(res.status_code, 200)
        self.member.refresh_from_db()
        self.assertEqual(self.member.first_name, 'Patricia')


class DateValidationTests(TestCase):
    """Birth/death dates can't be in the future, and death can't come before birth."""

    def setUp(self):
        from datetime import timedelta
        from django.utils import timezone
        self.owner = make_user('dateowner')
        self.tree = make_tree(self.owner)
        self.client = client_for(self.owner)
        self.today = timezone.localdate()
        self.tomorrow = (self.today + timedelta(days=1)).isoformat()

    def _post(self, **extra):
        return self.client.post(
            '/api/family-members/', {'tree': self.tree.id, 'first_name': 'D', **extra}, format='json')

    def test_future_birth_date_rejected(self):
        res = self._post(birth_date=self.tomorrow)
        self.assertEqual(res.status_code, 400, res.content)
        self.assertIn('birth_date', res.json())

    def test_future_death_date_rejected(self):
        res = self._post(birth_date='1950-01-01', death_date=self.tomorrow)
        self.assertEqual(res.status_code, 400, res.content)
        self.assertIn('death_date', res.json())

    def test_death_before_birth_rejected(self):
        res = self._post(birth_date='1990-05-05', death_date='1980-01-01')
        self.assertEqual(res.status_code, 400, res.content)
        self.assertIn('death_date', res.json())

    def test_death_before_stored_birth_rejected_on_partial_update(self):
        m = FamilyMember.objects.create(
            tree=self.tree, first_name='P', birth_date='1990-05-05', created_by=self.owner)
        res = self.client.patch(
            f'/api/family-members/{m.id}/', {'death_date': '1980-01-01'}, format='json')
        self.assertEqual(res.status_code, 400, res.content)

    def test_valid_dates_accepted(self):
        res = self._post(birth_date='1950-01-01', death_date='2020-06-01')
        self.assertEqual(res.status_code, 201, res.content)
        res = self._post(birth_date=self.today.isoformat())
        self.assertEqual(res.status_code, 201, res.content)
