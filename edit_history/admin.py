from django.contrib import admin

from .models import EditHistory


@admin.register(EditHistory)
class EditHistoryAdmin(admin.ModelAdmin):
    """
    A record of what family members did, for reference. It is view-only on purpose, even for
    superusers: it can't be added to, edited or deleted here, and changes made in this admin
    site are not written to it (they are staff actions, not family edits).
    """

    list_display = ('edited_at', 'tree', 'entity_type', 'change_description', 'edited_by', 'by_staff')
    list_filter = ('by_staff', 'entity_type', 'tree')
    search_fields = ('change_description', 'tree__tree_name', 'edited_by__email')
    date_hierarchy = 'edited_at'
    list_select_related = ('tree', 'edited_by')
    show_full_result_count = False  # skip a COUNT(*) over the whole table on every page

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        # Deleting a tree (or a user, who owns trees) removes its history with it, and Django's
        # admin refuses that whole delete if any model it would cascade into says "no". So the
        # history may go as part of those cascades, but never from this model's own pages.
        match = request.resolver_match
        own_pages = bool(match and match.url_name and match.url_name.startswith('edit_history_edithistory_'))
        return not own_pages
