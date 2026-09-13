from django.db import models
from family_trees.models import FamilyTree
from family_codes.models import FamilyCode
from users.models import User


class JoinRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    tree = models.ForeignKey(
        FamilyTree, on_delete=models.CASCADE, related_name='join_requests'
    )
    requester = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='join_requests'
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    message = models.TextField(blank=True)
    family_code_used = models.ForeignKey(
        FamilyCode, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='join_requests'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'join_requests'

    def __str__(self):
        return f'{self.requester.email} -> {self.tree.tree_name} ({self.status})'
