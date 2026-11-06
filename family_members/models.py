from django.db import models
from users.models import User
from family_trees.models import FamilyTree


class FamilyMember(models.Model):
    GENDER_CHOICES = [('male', 'Male'), ('female', 'Female'), ('other', 'Other')]

    tree = models.ForeignKey(
        FamilyTree, on_delete=models.CASCADE, related_name='family_members'
    )
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='family_member_profiles'
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)
    # Optional (blank = not recorded). Used so relationships read "Father/Son/..." not "Parent/Child".
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, default='')
    phone = models.CharField(max_length=20, blank=True)
    # Public: tree members and communities (if the tree is shared) can see it. Private: only the
    # tree owner and the person themself (their linked account) can.
    phone_public = models.BooleanField(default=False)
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


class StaffDeletedMember(models.Model):
    """
    A person a superuser deleted through staff edit mode, kept in full so the delete can be undone.

    This is the ONLY place a deleted person's private phone number and account link survive, which is
    why it is locked down on purpose:
      * no serializer, no list/detail API for ordinary users, and it is not registered in the Django
        admin; the only code that reads it is the superuser-only restore code (family_trees/staff_write.py);
      * rows are one-shot (deleted as soon as they are restored) and expire after
        settings.STAFF_RESTORE_RETENTION_DAYS (30 by default); expired rows are purged;
      * it is written in the same transaction as the delete, so a staff delete never happens without it.
    """

    tree = models.ForeignKey(FamilyTree, on_delete=models.CASCADE, related_name='staff_deleted_members')
    original_member_id = models.IntegerField()
    # Display only, for the staff "recently deleted" list. The real data is in `person` / `links`.
    name = models.CharField(max_length=255)
    deleted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')
    deleted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(db_index=True)
    person = models.TextField(help_text='JSON: every column of the deleted person, private ones included.')
    links = models.TextField(help_text='JSON: every relationship the person was in.')

    class Meta:
        db_table = 'staff_deleted_members'
        ordering = ['-deleted_at']

    def __str__(self):
        return f'Deleted person #{self.original_member_id} ({self.name}) in tree {self.tree_id}'
