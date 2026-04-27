from django.db import models
from family_trees.models import FamilyTree
from family_members.models import FamilyMember
from users.models import User


class RelationshipType(models.Model):
    CATEGORY_CHOICES = [
        ('biological', 'Biological'),
        ('adoptive', 'Adoptive'),
        ('step', 'Step'),
        ('guardianship', 'Guardianship'),
        ('marriage', 'Marriage'),
    ]

    type_name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'relationship_types'

    def __str__(self):
        return self.type_name


class Relationship(models.Model):
    tree = models.ForeignKey(
        FamilyTree, on_delete=models.CASCADE, related_name='relationships'
    )
    member_1 = models.ForeignKey(
        FamilyMember, on_delete=models.CASCADE, related_name='relationships_as_member1'
    )
    member_2 = models.ForeignKey(
        FamilyMember, on_delete=models.CASCADE, related_name='relationships_as_member2'
    )
    relationship_type = models.ForeignKey(
        RelationshipType, on_delete=models.CASCADE
    )
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='created_relationships'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'relationships'

    def __str__(self):
        return f'{self.member_1} → {self.relationship_type} → {self.member_2}'
