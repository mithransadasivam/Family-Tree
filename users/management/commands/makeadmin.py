"""
Give an EXISTING account access to the Django admin site (/admin/) and, optionally, set the
password it signs in with there.

Accounts here are created by Google sign-in and have no usable password, so the admin needs one
set once. The password is never taken on the command line (it would land in shell history and
process lists): you are prompted for it, or it is read from an environment variable.

    python manage.py makeadmin you@example.com                     # prompts twice for a password
    python manage.py makeadmin you@example.com --password-env PW   # reads it from $PW
    python manage.py makeadmin you@example.com --no-password       # grant access, keep password as is

It never creates accounts: the person must have signed in with Google at least once.
"""
import getpass
import os

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from users.models import User

MIN_PASSWORD_LENGTH = 12  # this account can edit and delete everything


class Command(BaseCommand):
    help = 'Make an existing account staff + superuser for /admin/, and set its password.'

    def add_arguments(self, parser):
        parser.add_argument('email', help='Email of the existing account')
        group = parser.add_mutually_exclusive_group()
        group.add_argument('--password-env', metavar='VAR', help='Read the new password from this environment variable')
        group.add_argument('--no-password', action='store_true', help='Only grant access; leave the password untouched')

    def handle(self, *args, email, password_env=None, no_password=False, **options):
        user = User.objects.filter(email__iexact=email.strip()).first()
        if user is None:
            raise CommandError(
                f'No account with email {email!r}. Sign in to the app with Google once first; '
                'this command only upgrades existing accounts.'
            )

        password = None
        if not no_password:
            password = self.read_password(password_env)

        with transaction.atomic():
            user.is_active = True
            user.is_staff = True
            user.is_superuser = True
            if password is not None:
                user.set_password(password)
            user.save()

        self.stdout.write(self.style.SUCCESS(
            f'{user.email} is now staff + superuser'
            + (' and the admin password has been set.' if password is not None else '; password unchanged.')
        ))

    def read_password(self, env_var):
        if env_var:
            password = os.environ.get(env_var)
            if not password:
                raise CommandError(f'Environment variable {env_var} is not set or is empty.')
        else:
            password = getpass.getpass('New admin password: ')
            if password != getpass.getpass('Repeat password: '):
                raise CommandError('The two passwords did not match. Nothing was changed.')
        if len(password) < MIN_PASSWORD_LENGTH:
            raise CommandError(f'Use at least {MIN_PASSWORD_LENGTH} characters: this account can change and delete everything.')
        return password
