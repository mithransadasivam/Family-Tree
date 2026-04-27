from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import EditHistory
from .serializers import EditHistorySerializer
from family_trees.models import TreeMember
from users.models import User


def get_current_user(request):
    user_id = request.auth.payload.get('user_id')
    return User.objects.get(id=user_id)


class EditHistoryListView(APIView):
    def get(self, request):
        tree_id = request.query_params.get('tree_id')
        user = get_current_user(request)
        if not tree_id:
            return Response({'error': 'tree_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not TreeMember.objects.filter(tree_id=tree_id, user=user).exists():
            return Response({'error': 'Not a member'}, status=status.HTTP_403_FORBIDDEN)
        history = EditHistory.objects.filter(tree_id=tree_id)
        return Response(EditHistorySerializer(history, many=True).data)
