import random
import string
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import FamilyCode
from family_trees.models import FamilyTree, TreeMember
from users.models import User
from edit_history.utils import log_edit


def get_current_user(request):
    user_id = request.auth.payload.get('user_id')
    return User.objects.get(id=user_id)


def generate_unique_code(tree_name):
    prefix = ''.join(c for c in tree_name.upper() if c.isalpha())[:6]
    suffix = ''.join(random.choices(string.digits, k=4))
    code = prefix + suffix
    while FamilyCode.objects.filter(code=code).exists():
        suffix = ''.join(random.choices(string.digits, k=4))
        code = prefix + suffix
    return code


class GenerateCodeView(APIView):
    def post(self, request):
        user = get_current_user(request)
        tree_id = request.data.get('tree_id')
        try:
            tree = FamilyTree.objects.get(id=tree_id)
        except FamilyTree.DoesNotExist:
            return Response({'error': 'Tree not found'}, status=status.HTTP_404_NOT_FOUND)
        if tree.owner != user:
            return Response({'error': 'Only the owner can generate codes'}, status=status.HTTP_403_FORBIDDEN)
        code = generate_unique_code(tree.tree_name)
        family_code = FamilyCode.objects.create(tree=tree, code=code, created_by=user)
        log_edit(tree, 'family_code', family_code.id, user, f'Generated family code: {code}')
        return Response({'code': code, 'tree': tree.tree_name}, status=status.HTTP_201_CREATED)


class RedeemCodeView(APIView):
    def post(self, request):
        user = get_current_user(request)
        code = request.data.get('code', '').upper().strip()
        try:
            family_code = FamilyCode.objects.get(code=code)
        except FamilyCode.DoesNotExist:
            return Response({'error': 'Invalid code'}, status=status.HTTP_404_NOT_FOUND)
        if family_code.is_used:
            return Response({'error': 'This code has already been used'}, status=status.HTTP_400_BAD_REQUEST)
        tree = family_code.tree
        if TreeMember.objects.filter(tree=tree, user=user).exists():
            return Response({'error': 'You are already a member of this tree'}, status=status.HTTP_400_BAD_REQUEST)
        TreeMember.objects.create(tree=tree, user=user, role='member')
        family_code.is_used = True
        family_code.used_by = user
        family_code.used_at = timezone.now()
        family_code.save()
        log_edit(tree, 'tree_member', user.id, user, f'{user.email} joined via code {code}')
        from family_trees.serializers import FamilyTreeSerializer
        return Response({
            'message': f'Successfully joined {tree.tree_name}',
            'tree': FamilyTreeSerializer(tree).data
        }, status=status.HTTP_200_OK)
