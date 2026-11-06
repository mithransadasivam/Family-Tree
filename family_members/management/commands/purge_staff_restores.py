"""
Delete expired staff-restore stashes (people a superuser deleted more than STAFF_RESTORE_RETENTION_DAYS
ago, kept in full so the delete could be undone).

Expired stashes are also purged opportunistically whenever staff delete or restore someone, so this is
only needed to keep the private data from lingering when nobody has used staff edit mode for a while.
Run it on a schedule (e.g. daily):

    python manage.py purge_staff_restores
"""
from django.core.management.base import BaseCommand

from family_members.restore import purge_expired


class Command(BaseCommand):
    help = 'Delete expired staff-restore stashes.'

    def handle(self, *args, **options):
        n = purge_expired()
        self.stdout.write(f'Purged {n} expired staff-restore stash{"" if n == 1 else "es"}.')
