from rest_framework import serializers
from .models import User, UserAvatar, UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['bio', 'location', 'phone', 'email', 'photo_url']


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    # True when the user uploaded their own picture; avatar_version changes whenever it does, so
    # clients can bust their image cache. Fetch it from GET /api/users/me/avatar/.
    has_avatar = serializers.SerializerMethodField()
    avatar_version = serializers.SerializerMethodField()

    def _avatar_time(self, obj):
        if not hasattr(obj, '_avatar_time'):
            obj._avatar_time = (
                UserAvatar.objects.filter(user_id=obj.id).values_list('updated_at', flat=True).first()
            )
        return obj._avatar_time

    def get_has_avatar(self, obj):
        return self._avatar_time(obj) is not None

    def get_avatar_version(self, obj):
        ts = self._avatar_time(obj)
        return int(ts.timestamp()) if ts else None

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name',
            'phone', 'address', 'photo_url', 'created_at', 'profile',
            'has_avatar', 'avatar_version'
        ]
        # email is the account's identity and photo_url is refreshed from Google at every sign-in,
        # so neither can be changed through the profile endpoint.
        read_only_fields = ['id', 'email', 'photo_url', 'created_at']
