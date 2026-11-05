"""
Superuser-only, READ-ONLY browsing of every family tree, for the website's staff pages.

This is deliberately a separate door. The normal endpoints (members, relationships, history,
trees) keep their rule "you must be a member of an active tree" for everyone, superusers
included; nothing there was loosened. Only these two GET endpoints look across trees.
"""
import logging

from django.db.models import Count, Q
from rest_framework import serializers, status
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from family_members.models import FamilyMember
from family_members.serializers import FamilyMemberSerializer
from relationships.models import Relationship
from relationships.serializers import RelationshipSerializer
from users.serializers import PublicUserSerializer

from .models import FamilyTree

log = logging.getLogger('kinship.staff')

DEFAULT_LIMIT = 100
MAX_LIMIT = 500


class IsSuperuser(BasePermission):
    """Signed in, active and a superuser. The user is re-read from the database on every
    request, so revoking the flag (or deactivating the account) takes effect immediately."""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_active and user.is_superuser)


class StaffTreeSerializer(serializers.ModelSerializer):
    owner = PublicUserSerializer(read_only=True)
    # Accounts that belong to the tree vs. people drawn in it.
    account_count = serializers.IntegerField(read_only=True)
    people_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = FamilyTree
        fields = ['id', 'tree_name', 'description', 'owner', 'is_active', 'approval_required',
                  'account_count', 'people_count', 'created_at', 'updated_at']
        read_only_fields = fields


def with_counts(queryset):
    return queryset.select_related('owner').annotate(
        account_count=Count('tree_members', distinct=True),
        people_count=Count('family_members', distinct=True),
    )


class StaffTreeListView(APIView):
    permission_classes = [IsSuperuser]
    http_method_names = ['get', 'head', 'options']

    def get(self, request):
        try:
            limit = min(MAX_LIMIT, max(1, int(request.query_params.get('limit', DEFAULT_LIMIT))))
            offset = max(0, int(request.query_params.get('offset', 0)))
        except ValueError:
            return Response({'error': 'limit and offset must be numbers'}, status=status.HTTP_400_BAD_REQUEST)

        trees = with_counts(FamilyTree.objects.all()).order_by('-created_at', '-id')
        q = (request.query_params.get('q') or '').strip()
        if q:
            trees = trees.filter(
                Q(tree_name__icontains=q) | Q(owner__email__icontains=q)
                | Q(owner__first_name__icontains=q) | Q(owner__last_name__icontains=q)
            )
        total = trees.count()
        log.info('staff_view user=%s list q=%r offset=%s limit=%s', request.user.id, q, offset, limit)
        return Response({
            'count': total,
            'results': StaffTreeSerializer(trees[offset:offset + limit], many=True).data,
        })


class StaffTreeDetailView(APIView):
    permission_classes = [IsSuperuser]
    http_method_names = ['get', 'head', 'options']

    def get(self, request, tree_id):
        tree = with_counts(FamilyTree.objects.filter(id=tree_id)).first()
        if tree is None:
            return Response({'error': 'Tree not found'}, status=status.HTTP_404_NOT_FOUND)
        log.info('staff_view user=%s tree=%s active=%s', request.user.id, tree.id, tree.is_active)
        members = FamilyMember.objects.filter(tree=tree).select_related('tree')
        relationships = Relationship.objects.filter(tree=tree)
        return Response({
            'tree': StaffTreeSerializer(tree).data,
            # viewer = the staff user, who is not the owner: private phone numbers come back blank.
            'members': FamilyMemberSerializer(members, many=True, context={'viewer': request.user}).data,
            'relationships': RelationshipSerializer(relationships, many=True).data,
        })
