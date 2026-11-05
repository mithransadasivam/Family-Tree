from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.forms import BaseUserCreationForm

from .models import User


class UserCreationForm(BaseUserCreationForm):
    """Django's default form is built around `username`; this site signs people in by email."""

    class Meta:
        model = User
        fields = ('email', 'google_id')


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    # Normal users are created by Google sign-in. Deleting one here also deletes the trees they
    # own (and everything in them), so the confirmation page lists exactly what will go.
    add_form = UserCreationForm
    ordering = ('email',)
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_superuser', 'is_active', 'created_at')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    search_fields = ('email', 'first_name', 'last_name', 'google_id')
    readonly_fields = ('last_login', 'created_at', 'updated_at')
    filter_horizontal = ('groups', 'user_permissions')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone', 'address', 'photo_url', 'google_id')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    add_fieldsets = (
        (None, {'classes': ('wide',), 'fields': ('email', 'google_id', 'password1', 'password2')}),
    )
