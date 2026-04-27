from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, UserProfile
from .serializers import UserSerializer, UserProfileSerializer
from utils.google_auth import verify_google_token


def get_tokens_for_user(user):
    refresh = RefreshToken()
    refresh['user_id'] = user.id
    refresh['email'] = user.email
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


class GoogleAuthView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        id_token = request.data.get('id_token')
        if not id_token:
            return Response(
                {'error': 'id_token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            google_user = verify_google_token(id_token)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_401_UNAUTHORIZED
            )

        user, created = User.objects.get_or_create(
            google_id=google_user['google_id'],
            defaults={
                'email': google_user['email'],
                'first_name': google_user['first_name'],
                'last_name': google_user['last_name'],
                'photo_url': google_user['photo_url'],
            }
        )

        if not created:
            user.photo_url = google_user['photo_url']
            user.save()

        if created:
            UserProfile.objects.create(user=user)

        tokens = get_tokens_for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'tokens': tokens,
            'is_new_user': created,
        }, status=status.HTTP_200_OK)


class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            payload = request.auth.payload
            print('PAYLOAD:', payload)
            user_id = payload.get('user_id')
            print('USER ID:', user_id)
            user = User.objects.get(id=user_id)
            return Response(UserSerializer(user).data)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    def patch(self, request):
        try:
            user_id = request.auth.payload.get('user_id')
            user = User.objects.get(id=user_id)
            serializer = UserSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
