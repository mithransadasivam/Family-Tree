"""
Superuser-only WRITE access to any family tree, for the website's staff edit mode.

Why a separate door rather than a superuser exemption inside the normal views: the normal views
(family_members/views.py, relationships/views.py) keep their rules for everyone - you must be a
member of an active tree, and only the owner deletes (H9) - and contain no `is_superuser` branch at
all, so there is no way for a regular user to reach a bypass that does not exist there. Everything
here is reachable only through IsSuperuser, declared once on StaffWriteView.

What a superuser does NOT get past, because these are integrity rules rather than permissions: the
sanity rules (one link per pair, no parent loops, no deleting a parent who has children), the
refusal to write to a tree its owner deleted, and the fixed list of editable fields.

The tree always comes from the URL, never from the request body, and every person or link is
looked up inside that tree, so a call can only touch the tree it names.
"""
import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from family_members import restore as member_restore
from family_members import services as member_services
from family_members.models import FamilyMember
from family_members.serializers import FamilyMemberSerializer
from relationships import services as relationship_services
from relationships.models import Relationship
from relationships.serializers import RelationshipSerializer
from utils.errors import ServiceError, error_response

from .models import FamilyTree
from .staff import IsSuperuser

log = logging.getLogger('kinship.staff')


def _refuse(message, code):
    return Response({'error': message}, status=code)


class StaffWriteView(APIView):
    """Base for every staff write endpoint. Only listed methods exist; everything else is a 405."""

    permission_classes = [IsSuperuser]

    def tree_for_write(self, tree_id):
        """(tree, None), or (None, error response) when it is missing or was deleted by its owner."""
        tree = FamilyTree.objects.filter(id=tree_id).first()
        if tree is None:
            return None, _refuse('Tree not found', status.HTTP_404_NOT_FOUND)
        if not tree.is_active:
            return None, _refuse(relationship_services.TREE_DELETED, status.HTTP_409_CONFLICT)
        return tree, None

    def body_for(self, request, tree):
        """The request body with `tree` pinned to the URL's tree. A body naming another tree is refused."""
        if not hasattr(request.data, 'get') or not hasattr(request.data, 'copy'):
            raise ServiceError({'error': 'Expected a JSON object'}, status.HTTP_400_BAD_REQUEST)
        data = request.data.copy()
        named = data.get('tree')
        if named not in (None, '') and str(named) != str(tree.id):
            raise ServiceError({'tree': ['This is not the family being edited']}, status.HTTP_400_BAD_REQUEST)
        data['tree'] = tree.id
        return data

    def record(self, request, action, tree, **ids):
        log.info('staff_write user=%s action=%s tree=%s %s', request.user.id, action, tree.id,
                 ' '.join(f'{k}={v}' for k, v in ids.items()))


def _person(tree, member_id):
    return FamilyMember.objects.filter(id=member_id, tree=tree).select_related('tree').first()


def _link(tree, rel_id):
    return Relationship.objects.filter(id=rel_id, tree=tree).select_related('tree').first()


class StaffMemberListView(StaffWriteView):
    http_method_names = ['post', 'options']

    def post(self, request, tree_id):
        tree, error = self.tree_for_write(tree_id)
        if error:
            return error
        try:
            member = member_services.create_member(tree.id, self.body_for(request, tree), request.user, staff=True)
        except ServiceError as e:
            return error_response(e)
        self.record(request, 'member_create', tree, member=member.id)
        return Response(FamilyMemberSerializer(member, context={'viewer': request.user}).data,
                        status=status.HTTP_201_CREATED)


class StaffMemberDetailView(StaffWriteView):
    http_method_names = ['patch', 'delete', 'options']

    def patch(self, request, tree_id, member_id):
        tree, error = self.tree_for_write(tree_id)
        if error:
            return error
        member = _person(tree, member_id)
        if member is None:
            return _refuse('Member not found', status.HTTP_404_NOT_FOUND)
        try:
            member = member_services.update_member(member, self.body_for(request, tree), request.user, staff=True)
        except ServiceError as e:
            return error_response(e)
        self.record(request, 'member_update', tree, member=member.id)
        return Response(FamilyMemberSerializer(member, context={'viewer': request.user}).data)

    def delete(self, request, tree_id, member_id):
        tree, error = self.tree_for_write(tree_id)
        if error:
            return error
        member = _person(tree, member_id)
        if member is None:
            return _refuse('Member not found', status.HTTP_404_NOT_FOUND)
        # No owner check here: removing a person is the owner's call for everyone ELSE (H9, enforced
        # in the normal view), and a superuser stands in for the owner. has_descendants still applies.
        try:
            stash = member_services.delete_member(member, request.user, staff=True)
        except ServiceError as e:
            return error_response(e)
        self.record(request, 'member_delete', tree, member=member_id)
        # restore_id lets staff undo this exactly (private phone and account link included) while the
        # stash lasts; it is just an id, none of the person's data is in this response.
        return Response({'message': 'Member deleted', 'restore_id': stash.id})


class StaffRelationshipListView(StaffWriteView):
    http_method_names = ['post', 'options']

    def post(self, request, tree_id):
        tree, error = self.tree_for_write(tree_id)
        if error:
            return error
        try:
            rel = relationship_services.create_relationship(tree.id, self.body_for(request, tree), request.user, staff=True)
        except ServiceError as e:
            return error_response(e)
        self.record(request, 'relationship_create', tree, relationship=rel.id)
        return Response(RelationshipSerializer(rel).data, status=status.HTTP_201_CREATED)


class StaffRelationshipDetailView(StaffWriteView):
    http_method_names = ['patch', 'delete', 'options']

    def patch(self, request, tree_id, rel_id):
        tree, error = self.tree_for_write(tree_id)
        if error:
            return error
        rel = _link(tree, rel_id)
        if rel is None:
            return _refuse('Not found', status.HTTP_404_NOT_FOUND)
        try:
            # The service only reads member_1 / member_2 / relationship_type from the body.
            rel = relationship_services.update_relationship(rel, self.body_for(request, tree), request.user, staff=True)
        except ServiceError as e:
            return error_response(e)
        self.record(request, 'relationship_update', tree, relationship=rel.id)
        return Response(RelationshipSerializer(rel).data)

    def delete(self, request, tree_id, rel_id):
        tree, error = self.tree_for_write(tree_id)
        if error:
            return error
        rel = _link(tree, rel_id)
        if rel is None:
            return _refuse('Not found', status.HTTP_404_NOT_FOUND)
        try:
            relationship_services.delete_relationship(rel, request.user, staff=True)
        except ServiceError as e:
            return error_response(e)
        self.record(request, 'relationship_delete', tree, relationship=rel_id)
        return Response({'message': 'Relationship deleted'})

class StaffRestoreListView(StaffWriteView):
    """People staff deleted from this tree who can still be restored: names and dates only."""

    http_method_names = ['get', 'options']

    def get(self, request, tree_id):
        if not FamilyTree.objects.filter(id=tree_id).exists():
            return _refuse('Tree not found', status.HTTP_404_NOT_FOUND)
        return Response([member_restore.stash_summary(s) for s in member_restore.live_stashes(tree_id)])


class StaffRestoreDetailView(StaffWriteView):
    """Restore one staff-deleted person from the stash: the exact row, private phone and account link included."""

    http_method_names = ['post', 'options']

    def post(self, request, tree_id, stash_id):
        tree, error = self.tree_for_write(tree_id)
        if error:
            return error
        try:
            result = member_restore.restore_member(tree.id, stash_id, request.user)
        except ServiceError as e:
            return error_response(e)
        self.record(request, 'member_restore', tree, member=result['member'].id)
        return Response({
            # viewer = the staff user, so a private phone number is still blanked in this answer.
            'member': FamilyMemberSerializer(result['member'], context={'viewer': request.user}).data,
            'restored_relationships': result['restored_links'],
            'skipped_relationships': result['skipped_links'],
            'account_link': result['account_link'],
        }, status=status.HTTP_200_OK)
