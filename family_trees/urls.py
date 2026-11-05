from django.urls import path
from .staff import StaffTreeDetailView, StaffTreeListView
from .views import FamilyTreeListView, FamilyTreeDetailView, LeaveTreeView

urlpatterns = [
    # Superuser-only, read-only look across all trees (see staff.py).
    path('staff/trees/', StaffTreeListView.as_view(), name='staff-tree-list'),
    path('staff/trees/<int:tree_id>/', StaffTreeDetailView.as_view(), name='staff-tree-detail'),
    path('family-trees/', FamilyTreeListView.as_view(), name='family-tree-list'),
    path('family-trees/<int:tree_id>/', FamilyTreeDetailView.as_view(), name='family-tree-detail'),
    path('family-trees/<int:tree_id>/leave/', LeaveTreeView.as_view(), name='leave-tree'),
]
