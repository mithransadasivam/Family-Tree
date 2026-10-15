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
from utils.throttles import CodeAttemptThrottle


def get_current_user(request):
    user_id = request.auth.payload.get('user_id')
    return User.objects.get(id=user_id)


# Unambiguous characters only (no 0/O or 1/I), so codes are easy to read out or type.
CODE_ALPHABET = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'


def generate_unique_code(tree_name):
    # A readable prefix from the tree's name, plus a random suffix that cannot be guessed
    # (32^6 combinations; the old 4-digit suffix had only 10,000).
    prefix = ''.join(c for c in tree_name.upper() if c.isalpha())[:6]
    while True:
        suffix = ''.join(random.SystemRandom().choices(CODE_ALPHABET, k=6))
        code = prefix + suffix
        if not FamilyCode.objects.filter(code=code).exists():
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
    throttle_classes = [CodeAttemptThrottle]

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
        if tree.approval_required:
            # Joining directly would skip the owner's approval. Join requests (POST
            # /api/join-requests/) are the path that honours the setting.
            return Response(
                {'error': "This tree needs the owner's approval. Send a join request instead."},
                status=status.HTTP_403_FORBIDDEN
            )
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
