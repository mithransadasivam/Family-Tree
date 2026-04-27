from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import FamilyTree, TreeMember
from .serializers import FamilyTreeSerializer
from users.models import User
from edit_history.utils import log_edit


def get_current_user(request):
    user_id = request.auth.payload.get('user_id')
    return User.objects.get(id=user_id)


class FamilyTreeListView(APIView):
    def get(self, request):
        user = get_current_user(request)
        memberships = TreeMember.objects.filter(user=user).values_list('tree_id', flat=True)
        trees = FamilyTree.objects.filter(id__in=memberships, is_active=True)
        return Response(FamilyTreeSerializer(trees, many=True).data)

    def post(self, request):
        user = get_current_user(request)
        serializer = FamilyTreeSerializer(data=request.data)
        if serializer.is_valid():
            tree = serializer.save(owner=user)
            TreeMember.objects.create(tree=tree, user=user, role='owner')
            log_edit(tree, 'family_tree', tree.id, user, f'Created tree: {tree.tree_name}')
            return Response(FamilyTreeSerializer(tree).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FamilyTreeDetailView(APIView):
    def get_tree(self, tree_id, user):
        try:
            tree = FamilyTree.objects.get(id=tree_id, is_active=True)
            if not TreeMember.objects.filter(tree=tree, user=user).exists():
                return None, Response({'error': 'Not a member'}, status=status.HTTP_403_FORBIDDEN)
            return tree, None
        except FamilyTree.DoesNotExist:
            return None, Response({'error': 'Tree not found'}, status=status.HTTP_404_NOT_FOUND)

    def get(self, request, tree_id):
        user = get_current_user(request)
        tree, error = self.get_tree(tree_id, user)
        if error:
            return error
        return Response(FamilyTreeSerializer(tree).data)

    def patch(self, request, tree_id):
        user = get_current_user(request)
        tree, error = self.get_tree(tree_id, user)
        if error:
            return error
        if tree.owner != user:
            return Response({'error': 'Only the owner can edit this tree'}, status=status.HTTP_403_FORBIDDEN)
        serializer = FamilyTreeSerializer(tree, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            log_edit(tree, 'family_tree', tree.id, user, f'Updated tree: {tree.tree_name}')
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, tree_id):
        user = get_current_user(request)
        tree, error = self.get_tree(tree_id, user)
        if error:
            return error
        if tree.owner != user:
            return Response({'error': 'Only the owner can delete this tree'}, status=status.HTTP_403_FORBIDDEN)
        tree.is_active = False
        tree.save()
        return Response({'message': 'Tree deleted'}, status=status.HTTP_200_OK)
