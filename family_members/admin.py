from django.contrib import admin

from .models import FamilyMember


@admin.register(FamilyMember)
class FamilyMemberAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'last_name', 'tree', 'gender', 'birth_date', 'death_date', 'created_by')
    list_filter = ('gender', 'phone_public')
    search_fields = ('first_name', 'last_name', 'tree__tree_name', 'created_by__email')
    raw_id_fields = ('tree', 'user', 'created_by')
