from django.urls import path
from .views import AvatarView, GoogleAuthView, LogoutView, TokenRefreshView, UserDetailView

urlpatterns = [
    path('auth/google/', GoogleAuthView.as_view(), name='google-auth'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('users/me/', UserDetailView.as_view(), name='user-detail'),
    path('users/me/avatar/', AvatarView.as_view(), name='user-avatar'),
]
