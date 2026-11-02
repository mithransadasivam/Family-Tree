from django.db import transaction
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from family_trees.models import FamilyTree
from users.models import User
from utils.throttles import CommunityFindThrottle, CommunitySearchThrottle
from .models import Community, CommunityJoinRequest, CommunityMember, CommunityTree
from .search import search_people

MAX_OWNED = 10


def current_user(request):
    return User.objects.get(id=request.auth.payload.get('user_id'))


def full_name(user):
    return f'{user.first_name} {user.last_name}'.strip() or user.email


def err(message, code=status.HTTP_400_BAD_REQUEST):
    return Response({'error': message}, status=code)


def membership(community, user):
    return CommunityMember.objects.filter(community=community, user=user).first()


def get_member_community(community_id, user):
    """(community, membership, error). Non-members get the same 404 as a missing community."""
    community = Community.objects.filter(id=community_id).first()
    mem = membership(community, user) if community else None
    if not mem:
        return None, None, err('Community not found', status.HTTP_404_NOT_FOUND)
    return community, mem, None


def remove_member(community, user):
    """Take someone out and stop sharing their trees, since they can no longer vouch for them."""
    CommunityTree.objects.filter(community=community, tree__owner=user).delete()
    CommunityMember.objects.filter(community=community, user=user).delete()


def summary(community, mem):
    return {
        'id': community.id,
        'name': community.name,
        'description': community.description,
        'role': mem.role,
        'member_count': community.memberships.count(),
        'tree_count': community.shared_trees.count(),
    }


class CommunityListView(APIView):
    def get(self, request):
        user = current_user(request)
        mems = CommunityMember.objects.filter(user=user).select_related('community').order_by('community__name')
        return Response([summary(m.community, m) for m in mems])

    def post(self, request):
        user = current_user(request)
        name = (request.data.get('name') or '').strip()
        description = (request.data.get('description') or '').strip()
        if not 2 <= len(name) <= 120:
            return err('Give the community a name (2 to 120 characters)')
        if len(description) > 500:
            return err('The description can be at most 500 characters')
        if Community.objects.filter(owner=user).count() >= MAX_OWNED:
            return err(f'You can own up to {MAX_OWNED} communities')
        with transaction.atomic():
            community = Community.objects.create(name=name, description=description, owner=user)
            mem = CommunityMember.objects.create(community=community, user=user, role='owner')
        return Response(summary(community, mem), status=status.HTTP_201_CREATED)


class CommunityFindView(APIView):
    """Look a community up by name so you can ask to join it. It never lists everything."""
    throttle_classes = [CommunityFindThrottle]

    def get(self, request):
        user = current_user(request)
        q = (request.query_params.get('q') or '').strip()
        if len(q) < 2:
            return Response([])
        found = list(Community.objects.filter(name__icontains=q).order_by('name')[:20])
        mine = set(CommunityMember.objects.filter(user=user, community__in=found).values_list('community_id', flat=True))
        pending = set(CommunityJoinRequest.objects.filter(
            requester=user, community__in=found, status='pending').values_list('community_id', flat=True))
        return Response([{
            'id': c.id,
            'name': c.name,
            'description': c.description,
            'member_count': c.memberships.count(),
            'status': 'member' if c.id in mine else 'pending' if c.id in pending else None,
        } for c in found])


class CommunityDetailView(APIView):
    def get(self, request, community_id):
        user = current_user(request)
        community, mem, error = get_member_community(community_id, user)
        if error:
            return error
        shared = set(community.shared_trees.values_list('tree_id', flat=True))
        data = summary(community, mem)
        data['my_trees'] = [
            {'id': t.id, 'tree_name': t.tree_name, 'shared': t.id in shared}
            for t in FamilyTree.objects.filter(owner=user, is_active=True).order_by('tree_name')
        ]
        if mem.role == 'owner':
            data['pending_requests'] = community.join_requests.filter(status='pending').count()
        return Response(data)

    def patch(self, request, community_id):
        user = current_user(request)
        community, mem, error = get_member_community(community_id, user)
        if error:
            return error
        if mem.role != 'owner':
            return err('Only the owner can edit the community', status.HTTP_403_FORBIDDEN)
        if 'name' in request.data:
            name = (request.data.get('name') or '').strip()
            if not 2 <= len(name) <= 120:
                return err('Give the community a name (2 to 120 characters)')
            community.name = name
        if 'description' in request.data:
            description = (request.data.get('description') or '').strip()
            if len(description) > 500:
                return err('The description can be at most 500 characters')
            community.description = description
        community.save()
        return Response(summary(community, mem))

    def delete(self, request, community_id):
        user = current_user(request)
        community, mem, error = get_member_community(community_id, user)
        if error:
            return error
        if mem.role != 'owner':
            return err('Only the owner can delete the community', status.HTTP_403_FORBIDDEN)
        community.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CommunityJoinView(APIView):
    throttle_classes = [CommunityFindThrottle]

    def post(self, request, community_id):
        user = current_user(request)
        community = Community.objects.filter(id=community_id).first()
        if not community:
            return err('Community not found', status.HTTP_404_NOT_FOUND)
        if membership(community, user):
            return err('You are already in this community')
        if CommunityJoinRequest.objects.filter(community=community, requester=user, status='pending').exists():
            return err('You already asked to join. The owner will review it.')
        message = (request.data.get('message') or '').strip()[:300]
        CommunityJoinRequest.objects.create(community=community, requester=user, message=message)
        return Response({'message': 'Request sent. The owner will review it.'}, status=status.HTTP_201_CREATED)


class CommunityLeaveView(APIView):
    def post(self, request, community_id):
        user = current_user(request)
        community, mem, error = get_member_community(community_id, user)
        if error:
            return error
        if mem.role == 'owner':
            return err('The owner cannot leave. Delete the community instead.')
        remove_member(community, user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CommunityRequestsView(APIView):
    def get(self, request, community_id):
        user = current_user(request)
        community, mem, error = get_member_community(community_id, user)
        if error:
            return error
        if mem.role != 'owner':
            return err('Only the owner can see join requests', status.HTTP_403_FORBIDDEN)
        pending = community.join_requests.filter(status='pending').select_related('requester')
        return Response([{
            'id': r.id,
            'name': full_name(r.requester),
            'email': r.requester.email,
            'message': r.message,
            'created_at': r.created_at,
        } for r in pending])


class CommunityRequestDetailView(APIView):
    def patch(self, request, request_id):
        user = current_user(request)
        join = CommunityJoinRequest.objects.select_related('community', 'requester').filter(id=request_id).first()
        if not join or join.community.owner_id != user.id:
            return err('Request not found', status.HTTP_404_NOT_FOUND)
        if join.status != 'pending':
            return err('This request has already been handled')
        new_status = request.data.get('status')
        if new_status not in ('approved', 'rejected'):
            return err("status must be 'approved' or 'rejected'")
        with transaction.atomic():
            join.status = new_status
            join.save()
            if new_status == 'approved':
                CommunityMember.objects.get_or_create(
                    community=join.community, user=join.requester, defaults={'role': 'member'})
        return Response({'id': join.id, 'status': join.status})


class CommunityMembersView(APIView):
    def get(self, request, community_id):
        user = current_user(request)
        community, mem, error = get_member_community(community_id, user)
        if error:
            return error
        if mem.role != 'owner':
            return err('Only the owner can see the member list', status.HTTP_403_FORBIDDEN)
        mems = community.memberships.select_related('user').order_by('joined_at')
        return Response([
            {'user_id': m.user_id, 'name': full_name(m.user), 'email': m.user.email, 'role': m.role}
            for m in mems
        ])


class CommunityMemberDetailView(APIView):
    def delete(self, request, community_id, user_id):
        user = current_user(request)
        community, mem, error = get_member_community(community_id, user)
        if error:
            return error
        if mem.role != 'owner':
            return err('Only the owner can remove members', status.HTTP_403_FORBIDDEN)
        if user_id == user.id:
            return err('You are the owner. Delete the community instead.')
        target = User.objects.filter(id=user_id).first()
        if not target or not membership(community, target):
            return err('Member not found', status.HTTP_404_NOT_FOUND)
        remove_member(community, target)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CommunityTreesView(APIView):
    """Share one of your own family trees with the community."""

    def post(self, request, community_id):
        user = current_user(request)
        community, mem, error = get_member_community(community_id, user)
        if error:
            return error
        tree = FamilyTree.objects.filter(id=request.data.get('tree_id'), owner=user, is_active=True).first()
        if not tree:
            return err('You can only share a family tree you own', status.HTTP_403_FORBIDDEN)
        CommunityTree.objects.get_or_create(community=community, tree=tree, defaults={'added_by': user})
        return Response({'tree_id': tree.id, 'shared': True}, status=status.HTTP_201_CREATED)


class CommunityTreeDetailView(APIView):
    def delete(self, request, community_id, tree_id):
        user = current_user(request)
        community, mem, error = get_member_community(community_id, user)
        if error:
            return error
        shared = CommunityTree.objects.filter(community=community, tree_id=tree_id).select_related('tree').first()
        if not shared:
            return err('That family is not shared here', status.HTTP_404_NOT_FOUND)
        if shared.tree.owner_id != user.id and mem.role != 'owner':
            return err('Only the family owner or the community owner can stop sharing it', status.HTTP_403_FORBIDDEN)
        shared.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CommunityPeopleView(APIView):
    throttle_classes = [CommunitySearchThrottle]

    def get(self, request, community_id):
        user = current_user(request)
        community, mem, error = get_member_community(community_id, user)
        if error:
            return error
        try:
            total, results = search_people(community, request.query_params)
        except ValueError as e:
            return err(str(e))
        return Response({'count': total, 'results': results})
