from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Relationship, RelationshipType
from .serializers import RelationshipSerializer, RelationshipTypeSerializer
from family_trees.models import TreeMember
from users.models import User
from utils.errors import ServiceError, error_response
from . import services


def get_current_user(request):
    user_id = request.auth.payload.get('user_id')
    return User.objects.get(id=user_id)


class RelationshipTypeListView(APIView):
    def get(self, request):
        types = RelationshipType.objects.all()
        return Response(RelationshipTypeSerializer(types, many=True).data)


class RelationshipListView(APIView):
    def get(self, request):
        tree_id = request.query_params.get('tree_id')
        user = get_current_user(request)
        if not tree_id:
            return Response({'error': 'tree_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not TreeMember.objects.filter(tree_id=tree_id, tree__is_active=True, user=user).exists():
            return Response({'error': 'Not a member of this tree'}, status=status.HTTP_403_FORBIDDEN)
        relationships = Relationship.objects.filter(tree_id=tree_id)
        return Response(RelationshipSerializer(relationships, many=True).data)

    def post(self, request):
        user = get_current_user(request)
        tree_id = request.data.get('tree')
        if not TreeMember.objects.filter(tree_id=tree_id, tree__is_active=True, user=user).exists():
            return Response({'error': 'Not a member of this tree'}, status=status.HTTP_403_FORBIDDEN)
        try:
            rel = services.create_relationship(tree_id, request.data, user)
        except ServiceError as e:
            return error_response(e)
        return Response(RelationshipSerializer(rel).data, status=status.HTTP_201_CREATED)


class RelationshipDetailView(APIView):
    def patch(self, request, rel_id):
        """Change a relationship's type and/or either member. The tree itself cannot change."""
        user = get_current_user(request)
        try:
            rel = Relationship.objects.get(id=rel_id)
        except Relationship.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        if not TreeMember.objects.filter(tree=rel.tree, tree__is_active=True, user=user).exists():
            return Response({'error': 'Not a member'}, status=status.HTTP_403_FORBIDDEN)
        try:
            rel = services.update_relationship(rel, request.data, user)
        except ServiceError as e:
            return error_response(e)
        return Response(RelationshipSerializer(rel).data)

    def delete(self, request, rel_id):
        user = get_current_user(request)
        try:
            rel = Relationship.objects.get(id=rel_id)
        except Relationship.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        if not TreeMember.objects.filter(tree=rel.tree, tree__is_active=True, user=user).exists():
            return Response({'error': 'Not a member'}, status=status.HTTP_403_FORBIDDEN)
        # Any member may add and edit relationships, but removing one is the tree owner's call.
        if rel.tree.owner_id != user.id:
            return Response({'error': 'Only the tree owner can delete a relationship'},
                            status=status.HTTP_403_FORBIDDEN)
        try:
            services.delete_relationship(rel, user)
        except ServiceError as e:
            return error_response(e)
        return Response({'message': 'Relationship deleted'})
