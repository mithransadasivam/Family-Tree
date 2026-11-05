from rest_framework import serializers
from .models import FamilyTree, TreeMember
from users.serializers import PublicUserSerializer


class TreeMemberSerializer(serializers.ModelSerializer):
    user = PublicUserSerializer(read_only=True)

    class Meta:
        model = TreeMember
        fields = ['id', 'user', 'role', 'joined_at']


class FamilyTreeSerializer(serializers.ModelSerializer):
    owner = PublicUserSerializer(read_only=True)
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = FamilyTree
        fields = [
            'id', 'tree_name', 'description', 'owner',
            'member_count', 'approval_required', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']

    def get_member_count(self, obj):
        return obj.tree_members.count()
