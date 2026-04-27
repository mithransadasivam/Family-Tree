from rest_framework import serializers
from .models import EditHistory
from users.serializers import UserSerializer


class EditHistorySerializer(serializers.ModelSerializer):
    edited_by = UserSerializer(read_only=True)

    class Meta:
        model = EditHistory
        fields = [
            'id', 'entity_type', 'entity_id', 'field_name',
            'old_value', 'new_value', 'change_description',
            'edited_by', 'edited_at'
        ]
