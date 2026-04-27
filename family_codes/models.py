from django.db import models
from family_trees.models import FamilyTree
from users.models import User


class FamilyCode(models.Model):
    tree = models.ForeignKey(
        FamilyTree, on_delete=models.CASCADE, related_name='family_codes'
    )
    code = models.CharField(max_length=20, unique=True)
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='generated_codes'
    )
    used_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='redeemed_codes'
    )
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'family_codes'

    def __str__(self):
        return f'{self.code} ({"used" if self.is_used else "available"})'
