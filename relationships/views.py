from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Relationship, RelationshipType
from .serializers import RelationshipSerializer, RelationshipTypeSerializer
from family_trees.models import FamilyTree, TreeMember
from users.models import User
from edit_history.utils import log_edit


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
        if not TreeMember.objects.filter(tree_id=tree_id, user=user).exists():
            return Response({'error': 'Not a member of this tree'}, status=status.HTTP_403_FORBIDDEN)
        relationships = Relationship.objects.filter(tree_id=tree_id)
        return Response(RelationshipSerializer(relationships, many=True).data)

    def post(self, request):
        user = get_current_user(request)
        tree_id = request.data.get('tree')
        if not TreeMember.objects.filter(tree_id=tree_id, user=user).exists():
            return Response({'error': 'Not a member of this tree'}, status=status.HTTP_403_FORBIDDEN)
        serializer = RelationshipSerializer(data=request.data)
        if serializer.is_valid():
            rel = serializer.save(created_by=user)
            tree = FamilyTree.objects.get(id=tree_id)
            log_edit(tree, 'relationship', rel.id, user, f'Added relationship')
            return Response(RelationshipSerializer(rel).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RelationshipDetailView(APIView):
    def delete(self, request, rel_id):
        user = get_current_user(request)
        try:
            rel = Relationship.objects.get(id=rel_id)
            if not TreeMember.objects.filter(tree=rel.tree, user=user).exists():
                return Response({'error': 'Not a member'}, status=status.HTTP_403_FORBIDDEN)
            rel.delete()
            return Response({'message': 'Relationship deleted'})
        except Relationship.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
