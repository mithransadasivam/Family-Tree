from django.urls import path
from .views import GoogleAuthView, LogoutView, TokenRefreshView, UserDetailView

urlpatterns = [
    path('auth/google/', GoogleAuthView.as_view(), name='google-auth'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('users/me/', UserDetailView.as_view(), name='user-detail'),
]
