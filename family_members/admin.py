from django.contrib import admin

from .models import FamilyMember
from .serializers import can_see_phone

PRIVATE_PHONE = 'Hidden (private)'


@admin.register(FamilyMember)
class FamilyMemberAdmin(admin.ModelAdmin):
    """
    A person's phone number follows the same rule here as on the website's staff pages: a public number
    is shown, a private one is hidden from staff (it is visible only to the family's owner and the person
    themself, so a superuser who is neither does not see it). The number is never an editable form field
    here, so saving a person in the admin cannot overwrite or reveal it; the "public/private" flag is
    read-only for the same reason (the website's staff edit mode cannot change either).
    """

    list_display = ('id', 'first_name', 'last_name', 'tree', 'gender', 'birth_date', 'death_date', 'created_by')
    list_filter = ('gender', 'phone_public')
    search_fields = ('first_name', 'last_name', 'tree__tree_name', 'created_by__email')
    raw_id_fields = ('tree', 'user', 'created_by')
    exclude = ('phone',)
    readonly_fields = ('phone_public', 'phone_display')

    def get_object(self, request, object_id, from_field=None):
        # Remember WHO is looking on the person loaded for this request (not on the admin object, which
        # is shared between requests), so the display below can ask the same question the website does.
        obj = super().get_object(request, object_id, from_field)
        if obj is not None:
            obj._viewer = request.user
        return obj

    @admin.display(description='Phone')
    def phone_display(self, obj):
        if not obj.pk:  # the "add person" form: nothing to show yet
            return '-'
        # With no known viewer a private number stays hidden: the safe default.
        if not can_see_phone(obj, getattr(obj, '_viewer', None)):
            return PRIVATE_PHONE
        return obj.phone or '-'
