from rest_framework import serializers
from .models import FamilyMember


class FamilyMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = FamilyMember
        fields = [
            'id', 'tree', 'user', 'first_name', 'last_name',
            'phone', 'email', 'address', 'photo_url',
            'birth_date', 'birth_place', 'death_date', 'death_place',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']
