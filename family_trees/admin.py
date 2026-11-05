from django.contrib import admin

from .models import FamilyTree, TreeMember


class TreeMemberInline(admin.TabularInline):
    model = TreeMember
    extra = 0
    raw_id_fields = ('user',)


@admin.register(FamilyTree)
class FamilyTreeAdmin(admin.ModelAdmin):
    list_display = ('id', 'tree_name', 'owner', 'is_active', 'approval_required', 'created_at')
    list_filter = ('is_active', 'approval_required')
    search_fields = ('tree_name', 'owner__email')
    raw_id_fields = ('owner',)
    inlines = [TreeMemberInline]


@admin.register(TreeMember)
class TreeMemberAdmin(admin.ModelAdmin):
    list_display = ('id', 'tree', 'user', 'role', 'joined_at')
    list_filter = ('role',)
    search_fields = ('tree__tree_name', 'user__email')
    raw_id_fields = ('tree', 'user')
