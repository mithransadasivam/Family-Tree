from django.urls import path
from .staff import StaffTreeDetailView, StaffTreeListView
from .staff_write import (
    StaffMemberDetailView, StaffMemberListView, StaffRelationshipDetailView, StaffRelationshipListView,
    StaffRestoreDetailView, StaffRestoreListView,
)
from .views import FamilyTreeListView, FamilyTreeDetailView, LeaveTreeView

urlpatterns = [
    # Superuser-only, read-only look across all trees (see staff.py).
    path('staff/trees/', StaffTreeListView.as_view(), name='staff-tree-list'),
    path('staff/trees/<int:tree_id>/', StaffTreeDetailView.as_view(), name='staff-tree-detail'),
    # Superuser-only writes to any tree (see staff_write.py). The tree is always in the URL.
    path('staff/trees/<int:tree_id>/members/', StaffMemberListView.as_view(), name='staff-member-create'),
    path('staff/trees/<int:tree_id>/members/<int:member_id>/', StaffMemberDetailView.as_view(),
         name='staff-member-detail'),
    path('staff/trees/<int:tree_id>/relationships/', StaffRelationshipListView.as_view(),
         name='staff-relationship-create'),
    path('staff/trees/<int:tree_id>/relationships/<int:rel_id>/', StaffRelationshipDetailView.as_view(),
         name='staff-relationship-detail'),
    path('staff/trees/<int:tree_id>/restores/', StaffRestoreListView.as_view(), name='staff-restore-list'),
    path('staff/trees/<int:tree_id>/restores/<int:stash_id>/', StaffRestoreDetailView.as_view(),
         name='staff-restore-detail'),
    path('family-trees/', FamilyTreeListView.as_view(), name='family-tree-list'),
    path('family-trees/<int:tree_id>/', FamilyTreeDetailView.as_view(), name='family-tree-detail'),
    path('family-trees/<int:tree_id>/leave/', LeaveTreeView.as_view(), name='leave-tree'),
]
