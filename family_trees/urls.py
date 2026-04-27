from django.urls import path
from .views import FamilyTreeListView, FamilyTreeDetailView

urlpatterns = [
    path('family-trees/', FamilyTreeListView.as_view(), name='family-tree-list'),
    path('family-trees/<int:tree_id>/', FamilyTreeDetailView.as_view(), name='family-tree-detail'),
]
