from django.urls import path
from . import views

urlpatterns = [
    path('communities/', views.CommunityListView.as_view(), name='community-list'),
    path('communities/find/', views.CommunityFindView.as_view(), name='community-find'),
    path('communities/<int:community_id>/', views.CommunityDetailView.as_view(), name='community-detail'),
    path('communities/<int:community_id>/join/', views.CommunityJoinView.as_view(), name='community-join'),
    path('communities/<int:community_id>/leave/', views.CommunityLeaveView.as_view(), name='community-leave'),
    path('communities/<int:community_id>/requests/', views.CommunityRequestsView.as_view(), name='community-requests'),
    path('community-requests/<int:request_id>/', views.CommunityRequestDetailView.as_view(), name='community-request'),
    path('communities/<int:community_id>/members/', views.CommunityMembersView.as_view(), name='community-members'),
    path('communities/<int:community_id>/members/<int:user_id>/', views.CommunityMemberDetailView.as_view(), name='community-member'),
    path('communities/<int:community_id>/trees/', views.CommunityTreesView.as_view(), name='community-trees'),
    path('communities/<int:community_id>/trees/<int:tree_id>/', views.CommunityTreeDetailView.as_view(), name='community-tree'),
    path('communities/<int:community_id>/people/', views.CommunityPeopleView.as_view(), name='community-people'),
]
