from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import JoinRequest
from .serializers import JoinRequestSerializer
from family_codes.models import FamilyCode
from family_trees.models import FamilyTree, TreeMember
from users.models import User
from edit_history.utils import log_edit


def get_current_user(request):
    user_id = request.auth.payload.get('user_id')
    return User.objects.get(id=user_id)


class JoinRequestListCreateView(APIView):
    def get(self, request):
        user = get_current_user(request)
        tree_id = request.query_params.get('tree_id')
        if not tree_id:
            return Response({'error': 'tree_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            tree = FamilyTree.objects.get(id=tree_id)
        except FamilyTree.DoesNotExist:
            return Response({'error': 'Tree not found'}, status=status.HTTP_404_NOT_FOUND)
        if tree.owner != user:
            return Response({'error': 'Only the tree owner can view join requests'}, status=status.HTTP_403_FORBIDDEN)
        pending = JoinRequest.objects.filter(tree=tree, status='pending').order_by('-created_at')
        return Response(JoinRequestSerializer(pending, many=True).data)

    def post(self, request):
        user = get_current_user(request)
        code = request.data.get('code', '').upper().strip()
        message = request.data.get('message', '')
        try:
            family_code = FamilyCode.objects.get(code=code)
        except FamilyCode.DoesNotExist:
            return Response({'error': 'Invalid code'}, status=status.HTTP_404_NOT_FOUND)
        if family_code.is_used:
            return Response({'error': 'This code has already been used'}, status=status.HTTP_400_BAD_REQUEST)

        tree = family_code.tree
        if TreeMember.objects.filter(tree=tree, user=user).exists():
            return Response({'error': 'You are already a member of this tree'}, status=status.HTTP_400_BAD_REQUEST)
        if JoinRequest.objects.filter(tree=tree, requester=user, status='pending').exists():
            return Response({'error': 'You already have a pending request for this tree'}, status=status.HTTP_400_BAD_REQUEST)

        if not tree.approval_required:
            TreeMember.objects.create(tree=tree, user=user, role='member')
            family_code.is_used = True
            family_code.used_by = user
            family_code.used_at = timezone.now()
            family_code.save()
            join_request = JoinRequest.objects.create(
                tree=tree, requester=user, status='approved',
                message=message, family_code_used=family_code
            )
            log_edit(tree, 'tree_member', user.id, user, f'{user.email} auto-joined via code {code}')
            return Response({
                'auto_approved': True,
                'message': f'Successfully joined {tree.tree_name}',
                'request': JoinRequestSerializer(join_request).data,
            }, status=status.HTTP_201_CREATED)

        join_request = JoinRequest.objects.create(
            tree=tree, requester=user, status='pending',
            message=message, family_code_used=family_code
        )
        log_edit(tree, 'join_request', join_request.id, user, f'{user.email} requested to join via code {code}')
        return Response({
            'auto_approved': False,
            'message': 'Request sent! The tree owner will review your request.',
            'request': JoinRequestSerializer(join_request).data,
        }, status=status.HTTP_201_CREATED)


class JoinRequestDetailView(APIView):
    def patch(self, request, request_id):
        user = get_current_user(request)
        try:
            join_request = JoinRequest.objects.get(id=request_id)
        except JoinRequest.DoesNotExist:
            return Response({'error': 'Request not found'}, status=status.HTTP_404_NOT_FOUND)
        if join_request.tree.owner != user:
            return Response({'error': 'Only the tree owner can act on this request'}, status=status.HTTP_403_FORBIDDEN)
        if join_request.status != 'pending':
            return Response({'error': 'This request has already been handled'}, status=status.HTTP_400_BAD_REQUEST)

        new_status = request.data.get('status')
        if new_status not in ('approved', 'rejected'):
            return Response({'error': "status must be 'approved' or 'rejected'"}, status=status.HTTP_400_BAD_REQUEST)

        join_request.status = new_status
        join_request.save()

        if new_status == 'approved':
            TreeMember.objects.get_or_create(
                tree=join_request.tree, user=join_request.requester,
                defaults={'role': 'member'}
            )
            code = join_request.family_code_used
            if code and not code.is_used:
                code.is_used = True
                code.used_by = join_request.requester
                code.used_at = timezone.now()
                code.save()

        log_edit(
            join_request.tree, 'join_request', join_request.id, user,
            f'{new_status.capitalize()} join request from {join_request.requester.email}'
        )
        return Response(JoinRequestSerializer(join_request).data)


class MyJoinRequestsView(APIView):
    def get(self, request):
        user = get_current_user(request)
        requests_qs = JoinRequest.objects.filter(requester=user).order_by('-created_at')
        return Response(JoinRequestSerializer(requests_qs, many=True).data)
