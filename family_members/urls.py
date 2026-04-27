from django.urls import path
from .views import FamilyMemberListView, FamilyMemberDetailView

urlpatterns = [
    path('family-members/', FamilyMemberListView.as_view(), name='family-member-list'),
    path('family-members/<int:member_id>/', FamilyMemberDetailView.as_view(), name='family-member-detail'),
]
