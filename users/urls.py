from django.urls import path
from .views import GoogleAuthView, UserDetailView

urlpatterns = [
    path('auth/google/', GoogleAuthView.as_view(), name='google-auth'),
    path('users/me/', UserDetailView.as_view(), name='user-detail'),
]
