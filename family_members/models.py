from django.db import models
from users.models import User
from family_trees.models import FamilyTree


class FamilyMember(models.Model):
    tree = models.ForeignKey(
        FamilyTree, on_delete=models.CASCADE, related_name='family_members'
    )
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='family_member_profiles'
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    photo_url = models.URLField(max_length=500, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    birth_place = models.CharField(max_length=255, blank=True)
    death_date = models.DateField(null=True, blank=True)
    death_place = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='created_members'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'family_members'

    def __str__(self):
        return f'{self.first_name} {self.last_name}'
