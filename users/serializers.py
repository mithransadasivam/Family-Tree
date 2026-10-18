from rest_framework import serializers
from .models import User, UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['bio', 'location', 'phone', 'email', 'photo_url']


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name',
            'phone', 'address', 'photo_url', 'created_at', 'profile'
        ]
        # email is the account's identity and photo_url is refreshed from Google at every sign-in,
        # so neither can be changed through the profile endpoint.
        read_only_fields = ['id', 'email', 'photo_url', 'created_at']
