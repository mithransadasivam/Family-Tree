from django.conf import settings
from django.contrib import admin
from django.http import FileResponse, Http404
from django.urls import path, include, re_path


def webapp_index(request, *args, **kwargs):
    """Single-page app entry point: any non-API path loads the website, which routes itself."""
    index = settings.WEBAPP_DIR / 'index.html'
    if not index.is_file():
        raise Http404('Web app not built')
    return FileResponse(open(index, 'rb'), content_type='text/html; charset=utf-8')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('users.urls')),
    path('api/', include('family_trees.urls')),
    path('api/', include('family_members.urls')),
    path('api/', include('relationships.urls')),
    path('api/', include('family_codes.urls')),
    path('api/', include('edit_history.urls')),
    path('api/', include('join_requests.urls')),
    # Must stay last: everything not claimed above (and not a real file WhiteNoise already
    # served) is a page of the website.
    re_path(r'^(?!api/|admin/|static/).*$', webapp_index),
]
