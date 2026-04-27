from django.db import models
from family_trees.models import FamilyTree
from users.models import User


class EditHistory(models.Model):
    tree = models.ForeignKey(
        FamilyTree, on_delete=models.CASCADE, related_name='edit_history'
    )
    entity_type = models.CharField(max_length=50)
    entity_id = models.IntegerField()
    field_name = models.CharField(max_length=100, blank=True)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    change_description = models.TextField()
    edited_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='edit_history'
    )
    edited_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'edit_history'
        ordering = ['-edited_at']

    def __str__(self):
        return f'{self.entity_type} #{self.entity_id} — {self.change_description}'
