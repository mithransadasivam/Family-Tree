from django.core.management.base import BaseCommand
from users.models import User, UserProfile
from users.views import get_tokens_for_user

class Command(BaseCommand):
    def handle(self, *args, **options):
        user, created = User.objects.get_or_create(
            email='test@family.com',
            defaults={'google_id': 'testuser123', 'first_name': 'Test', 'last_name': 'User'}
        )
        if created:
            UserProfile.objects.create(user=user)
        tokens = get_tokens_for_user(user)
        self.stdout.write(tokens['access'])
