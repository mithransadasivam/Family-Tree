from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('users.urls')),
    path('api/', include('family_trees.urls')),
    path('api/', include('family_members.urls')),
    path('api/', include('relationships.urls')),
    path('api/', include('family_codes.urls')),
    path('api/', include('edit_history.urls')),
]
