from django.urls import path
from .views import RelationshipListView, RelationshipDetailView, RelationshipTypeListView

urlpatterns = [
    path('relationships/', RelationshipListView.as_view(), name='relationship-list'),
    path('relationships/<int:rel_id>/', RelationshipDetailView.as_view(), name='relationship-detail'),
    path('relationship-types/', RelationshipTypeListView.as_view(), name='relationship-type-list'),
]
