from rest_framework import serializers
from .models import JoinRequest


class JoinRequestSerializer(serializers.ModelSerializer):
    tree_name = serializers.CharField(source='tree.tree_name', read_only=True)
    requester_name = serializers.SerializerMethodField()
    requester_email = serializers.CharField(source='requester.email', read_only=True)

    class Meta:
        model = JoinRequest
        fields = [
            'id', 'tree', 'tree_name', 'requester', 'requester_name', 'requester_email',
            'status', 'message', 'family_code_used', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'tree', 'requester', 'status', 'family_code_used',
            'created_at', 'updated_at',
        ]

    def get_requester_name(self, obj):
        full_name = f'{obj.requester.first_name} {obj.requester.last_name}'.strip()
        return full_name or obj.requester.email
