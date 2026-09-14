from django.urls import path
from .views import FamilyTreeListView, FamilyTreeDetailView, LeaveTreeView

urlpatterns = [
    path('family-trees/', FamilyTreeListView.as_view(), name='family-tree-list'),
    path('family-trees/<int:tree_id>/', FamilyTreeDetailView.as_view(), name='family-tree-detail'),
    path('family-trees/<int:tree_id>/leave/', LeaveTreeView.as_view(), name='leave-tree'),
]
