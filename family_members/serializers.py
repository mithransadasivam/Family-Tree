from rest_framework import serializers
from .models import FamilyMember


def can_see_phone(member, viewer):
    """Public numbers are visible to the tree; private ones only to the tree owner and the person themself."""
    if member.phone_public:
        return True
    return viewer is not None and (member.tree.owner_id == viewer.id or member.user_id == viewer.id)


class FamilyMemberSerializer(serializers.ModelSerializer):
    """Pass context={'viewer': user}: a private phone number is blanked for anyone not allowed to see it."""

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if not can_see_phone(instance, self.context.get('viewer')):
            data['phone'] = ''
        return data

    def validate_tree(self, tree):
        # A person never changes family: moving one into another tree would let any member plant
        # data in a tree they don't belong to (or strand the person's relationships).
        if self.instance is not None and tree.id != self.instance.tree_id:
            raise serializers.ValidationError('A person cannot be moved to a different family')
        return tree

    def validate(self, attrs):
        # `user` links a person to a sign-in account, and that account can read the person's
        # private phone (see can_see_phone). So it is the owner's call: if anyone could set it,
        # a member could link themselves to anyone and read their "private" number.
        if 'user' in attrs:
            viewer = self.context.get('viewer')
            tree = attrs.get('tree') or (self.instance.tree if self.instance else None)
            is_owner = viewer is not None and tree is not None and tree.owner_id == viewer.id
            new_user = attrs['user']
            current_id = self.instance.user_id if self.instance else None
            unchanged = (new_user.id if new_user else None) == current_id
            if not unchanged:
                if not is_owner:
                    if self.instance is None:
                        # Creating (e.g. the web's undo-restore resends the old link): just
                        # don't link anyone rather than failing the whole request.
                        del attrs['user']
                    else:
                        raise serializers.ValidationError(
                            {'user': 'Only the tree owner can link a person to an account'})
                elif new_user is not None and not new_user.tree_memberships.filter(tree=tree).exists():
                    raise serializers.ValidationError({'user': 'That account is not in this family'})
        return attrs

    class Meta:
        model = FamilyMember
        fields = [
            'id', 'tree', 'user', 'first_name', 'last_name', 'gender',
            'phone', 'phone_public', 'email', 'address', 'photo_url',
            'birth_date', 'birth_place', 'death_date', 'death_place',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']
