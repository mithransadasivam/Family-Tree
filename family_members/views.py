from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import FamilyMember
from .serializers import FamilyMemberSerializer
from family_trees.models import TreeMember
from users.models import User
from utils.errors import ServiceError, error_response
from . import services


def get_current_user(request):
    user_id = request.auth.payload.get('user_id')
    return User.objects.get(id=user_id)


class FamilyMemberListView(APIView):
    def get(self, request):
        tree_id = request.query_params.get('tree_id')
        user = get_current_user(request)
        if not tree_id:
            return Response({'error': 'tree_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not TreeMember.objects.filter(tree_id=tree_id, tree__is_active=True, user=user).exists():
            return Response({'error': 'Not a member of this tree'}, status=status.HTTP_403_FORBIDDEN)
        members = FamilyMember.objects.filter(tree_id=tree_id).select_related('tree')
        return Response(FamilyMemberSerializer(members, many=True, context={'viewer': user}).data)

    def post(self, request):
        user = get_current_user(request)
        tree_id = request.data.get('tree')
        if not TreeMember.objects.filter(tree_id=tree_id, tree__is_active=True, user=user).exists():
            return Response({'error': 'Not a member of this tree'}, status=status.HTTP_403_FORBIDDEN)
        try:
            member = services.create_member(tree_id, request.data, user)
        except ServiceError as e:
            return error_response(e)
        return Response(FamilyMemberSerializer(member, context={'viewer': user}).data, status=status.HTTP_201_CREATED)


class FamilyMemberDetailView(APIView):
    def get_member(self, member_id, user):
        try:
            member = FamilyMember.objects.get(id=member_id)
            if not TreeMember.objects.filter(tree=member.tree, tree__is_active=True, user=user).exists():
                return None, Response({'error': 'Not a member of this tree'}, status=status.HTTP_403_FORBIDDEN)
            return member, None
        except FamilyMember.DoesNotExist:
            return None, Response({'error': 'Member not found'}, status=status.HTTP_404_NOT_FOUND)

    def get(self, request, member_id):
        user = get_current_user(request)
        member, error = self.get_member(member_id, user)
        if error:
            return error
        return Response(FamilyMemberSerializer(member, context={'viewer': user}).data)

    def patch(self, request, member_id):
        user = get_current_user(request)
        member, error = self.get_member(member_id, user)
        if error:
            return error
        try:
            member = services.update_member(member, request.data, user)
        except ServiceError as e:
            return error_response(e)
        return Response(FamilyMemberSerializer(member, context={'viewer': user}).data)

    def delete(self, request, member_id):
        user = get_current_user(request)
        member, error = self.get_member(member_id, user)
        if error:
            return error
        # Any member may add and edit people, but removing one is the tree owner's call.
        if member.tree.owner_id != user.id:
            return Response({'error': 'Only the tree owner can delete a person'}, status=status.HTTP_403_FORBIDDEN)
        try:
            services.delete_member(member, user)
        except ServiceError as e:
            return error_response(e)
        return Response({'message': 'Member deleted'}, status=status.HTTP_200_OK)
