from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from .models import User, UserProfile
from .serializers import UserSerializer, UserProfileSerializer
from utils.google_auth import verify_google_token


def _cookie_options():
    return {
        'httponly': True,
        'secure': settings.AUTH_COOKIE_SECURE,
        'samesite': settings.AUTH_COOKIE_SAMESITE,
        'domain': settings.AUTH_COOKIE_DOMAIN,
    }


def set_auth_cookies(response, access=None, refresh=None):
    """Web clients get the JWTs as httpOnly cookies (invisible to page JavaScript)."""
    jwt_settings = settings.SIMPLE_JWT
    if access:
        response.set_cookie(
            settings.AUTH_COOKIE_ACCESS, access,
            max_age=int(jwt_settings['ACCESS_TOKEN_LIFETIME'].total_seconds()),
            path='/api/', **_cookie_options()
        )
    if refresh:
        response.set_cookie(
            settings.AUTH_COOKIE_REFRESH, refresh,
            max_age=int(jwt_settings['REFRESH_TOKEN_LIFETIME'].total_seconds()),
            path='/api/auth/', **_cookie_options()
        )


def clear_auth_cookies(response):
    opts = {'domain': settings.AUTH_COOKIE_DOMAIN, 'samesite': settings.AUTH_COOKIE_SAMESITE}
    response.delete_cookie(settings.AUTH_COOKIE_ACCESS, path='/api/', **opts)
    response.delete_cookie(settings.AUTH_COOKIE_REFRESH, path='/api/auth/', **opts)


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
    # No auth here: a stale access cookie must not turn a fresh sign-in into a 401.
    authentication_classes = []

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
        response = Response({
            'user': UserSerializer(user).data,
            'tokens': tokens,
            'is_new_user': created,
        }, status=status.HTTP_200_OK)
        set_auth_cookies(response, access=tokens['access'], refresh=tokens['refresh'])
        return response


class TokenRefreshView(APIView):
    """Issue a new access token from the refresh token (cookie for web, body for others)."""
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        raw = request.data.get('refresh') or request.COOKIES.get(settings.AUTH_COOKIE_REFRESH)
        if not raw:
            return Response({'error': 'refresh token is required'}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            access = str(RefreshToken(raw).access_token)
        except TokenError:
            response = Response({'error': 'Invalid or expired refresh token'},
                                status=status.HTTP_401_UNAUTHORIZED)
            clear_auth_cookies(response)
            return response
        response = Response({'access': access}, status=status.HTTP_200_OK)
        set_auth_cookies(response, access=access)
        return response


class LogoutView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        response = Response({'message': 'Logged out'}, status=status.HTTP_200_OK)
        clear_auth_cookies(response)
        return response


class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user_id = request.auth.payload.get('user_id')
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

