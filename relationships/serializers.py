from rest_framework import serializers
from .models import Relationship, RelationshipType


class RelationshipTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RelationshipType
        fields = ['id', 'type_name', 'category', 'description']


class RelationshipSerializer(serializers.ModelSerializer):
    relationship_type_name = serializers.CharField(source='relationship_type.type_name', read_only=True)

    class Meta:
        model = Relationship
        fields = [
            'id', 'tree', 'member_1', 'member_2',
            'relationship_type', 'relationship_type_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
