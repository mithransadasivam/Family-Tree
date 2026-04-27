from django.urls import path
from .views import EditHistoryListView

urlpatterns = [
    path('edit-history/', EditHistoryListView.as_view(), name='edit-history'),
]
