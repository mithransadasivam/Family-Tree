from django.urls import path
from .views import JoinRequestListCreateView, JoinRequestDetailView, MyJoinRequestsView

urlpatterns = [
    path('join-requests/mine/', MyJoinRequestsView.as_view(), name='join-request-mine'),
    path('join-requests/', JoinRequestListCreateView.as_view(), name='join-request-list-create'),
    path('join-requests/<int:request_id>/', JoinRequestDetailView.as_view(), name='join-request-detail'),
]
