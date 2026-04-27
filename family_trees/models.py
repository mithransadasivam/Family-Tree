from django.db import models
from users.models import User


class FamilyTree(models.Model):
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='owned_trees'
    )
    tree_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'family_trees'

    def __str__(self):
        return self.tree_name


class TreeMember(models.Model):
    ROLE_CHOICES = [('owner', 'Owner'), ('member', 'Member')]

    tree = models.ForeignKey(
        FamilyTree, on_delete=models.CASCADE, related_name='tree_members'
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='tree_memberships'
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tree_members'
        unique_together = ('tree', 'user')

    def __str__(self):
        return f'{self.user.email} in {self.tree.tree_name} ({self.role})'
