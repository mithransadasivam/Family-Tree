from django.contrib import admin

from .models import Relationship, RelationshipType


@admin.register(RelationshipType)
class RelationshipTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'type_name', 'category')
    list_filter = ('category',)
    search_fields = ('type_name',)


@admin.register(Relationship)
class RelationshipAdmin(admin.ModelAdmin):
    # "member_1 IS <type> OF member_2" - the list shows it that way round.
    list_display = ('id', 'tree', 'member_1', 'relationship_type', 'member_2', 'created_at')
    list_filter = ('relationship_type',)
    search_fields = ('tree__tree_name', 'member_1__first_name', 'member_2__first_name')
    raw_id_fields = ('tree', 'member_1', 'member_2', 'created_by')
