from django.contrib import admin

from .models import JoinRequest


@admin.register(JoinRequest)
class JoinRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'tree', 'requester', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('tree__tree_name', 'requester__email', 'message')
    raw_id_fields = ('tree', 'requester', 'family_code_used')
