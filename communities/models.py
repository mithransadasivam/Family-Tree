from django.db import models
from family_trees.models import FamilyTree
from users.models import User


class Community(models.Model):
    """A group such as a village or congregation. Its owner chooses who joins; members can search the
    people in the family trees that tree owners have chosen to share with it."""
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True, max_length=500)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_communities')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'communities'

    def __str__(self):
        return self.name


class CommunityMember(models.Model):
    ROLE_CHOICES = [('owner', 'Owner'), ('member', 'Member')]

    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='community_memberships')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'community_members'
        unique_together = ('community', 'user')


class CommunityJoinRequest(models.Model):
    STATUS_CHOICES = [('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')]

    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='join_requests')
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='community_join_requests')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    message = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'community_join_requests'
        ordering = ['-created_at']


class CommunityTree(models.Model):
    """A family tree its owner has chosen to share with a community (so its people show up in search)."""
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='shared_trees')
    tree = models.ForeignKey(FamilyTree, on_delete=models.CASCADE, related_name='shared_in')
    added_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'community_trees'
        unique_together = ('community', 'tree')
