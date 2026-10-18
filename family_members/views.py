from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import FamilyMember
from .serializers import FamilyMemberSerializer
from family_trees.models import FamilyTree, TreeMember
from users.models import User
from edit_history.utils import log_edit


def get_current_user(request):
    user_id = request.auth.payload.get('user_id')
    return User.objects.get(id=user_id)


# What a relationship type says about member_1 relative to member_2. A person who is the
# parent / grandparent of someone (member_1 of a "Father" link, or member_2 of a "Son" link)
# is a root of the tree: deleting them would orphan their descendants.
PARENT_TYPES = {
    'Father', 'Mother', 'Stepfather', 'Stepmother', 'Step Father', 'Step Mother',
    'Grandfather', 'Grandmother',
}
CHILD_TYPES = {
    'Son', 'Daughter', 'Stepson', 'Stepdaughter', 'Step Son', 'Step Daughter',
    'Adopted Son', 'Adopted Daughter', 'Grandson', 'Granddaughter',
}


def has_descendants(member):
    from relationships.models import Relationship
    return (
        Relationship.objects.filter(
            member_1=member, relationship_type__type_name__in=PARENT_TYPES
        ).exists()
        or Relationship.objects.filter(
            member_2=member, relationship_type__type_name__in=CHILD_TYPES
        ).exists()
    )


class FamilyMemberListView(APIView):
    def get(self, request):
        tree_id = request.query_params.get('tree_id')
        user = get_current_user(request)
        if not tree_id:
            return Response({'error': 'tree_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not TreeMember.objects.filter(tree_id=tree_id, user=user).exists():
            return Response({'error': 'Not a member of this tree'}, status=status.HTTP_403_FORBIDDEN)
        members = FamilyMember.objects.filter(tree_id=tree_id)
        return Response(FamilyMemberSerializer(members, many=True).data)

    def post(self, request):
        user = get_current_user(request)
        tree_id = request.data.get('tree')
        if not TreeMember.objects.filter(tree_id=tree_id, user=user).exists():
            return Response({'error': 'Not a member of this tree'}, status=status.HTTP_403_FORBIDDEN)
        serializer = FamilyMemberSerializer(data=request.data)
        if serializer.is_valid():
            member = serializer.save(created_by=user)
            tree = FamilyTree.objects.get(id=tree_id)
            log_edit(tree, 'family_member', member.id, user, f'Added member: {member.first_name} {member.last_name}')
            return Response(FamilyMemberSerializer(member).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FamilyMemberDetailView(APIView):
    def get_member(self, member_id, user):
        try:
            member = FamilyMember.objects.get(id=member_id)
            if not TreeMember.objects.filter(tree=member.tree, user=user).exists():
                return None, Response({'error': 'Not a member of this tree'}, status=status.HTTP_403_FORBIDDEN)
            return member, None
        except FamilyMember.DoesNotExist:
            return None, Response({'error': 'Member not found'}, status=status.HTTP_404_NOT_FOUND)

    def get(self, request, member_id):
        user = get_current_user(request)
        member, error = self.get_member(member_id, user)
        if error:
            return error
        return Response(FamilyMemberSerializer(member).data)

    def patch(self, request, member_id):
        user = get_current_user(request)
        member, error = self.get_member(member_id, user)
        if error:
            return error
        old_name = f'{member.first_name} {member.last_name}'
        serializer = FamilyMemberSerializer(member, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            log_edit(member.tree, 'family_member', member.id, user, f'Updated member: {old_name}')
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, member_id):
        user = get_current_user(request)
        member, error = self.get_member(member_id, user)
        if error:
            return error
        if has_descendants(member):
            return Response(
                {'error': f'{member.first_name} has children in the family and cannot be deleted. '
                          'Remove their children (or those relationships) first.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        name = f'{member.first_name} {member.last_name}'
        tree = member.tree
        member.delete()
        log_edit(tree, 'family_member', member_id, user, f'Deleted member: {name}')
        return Response({'message': 'Member deleted'}, status=status.HTTP_200_OK)
