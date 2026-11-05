from django.contrib import admin

from .models import FamilyCode


@admin.register(FamilyCode)
class FamilyCodeAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'tree', 'is_used', 'used_by', 'created_by', 'created_at')
    list_filter = ('is_used',)
    search_fields = ('code', 'tree__tree_name')
    raw_id_fields = ('tree', 'created_by', 'used_by')
