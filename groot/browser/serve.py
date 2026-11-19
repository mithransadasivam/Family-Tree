"""
Starts the throwaway Kinship server for Groot's browser tests and seeds three sign-in accounts.

    python groot/browser/serve.py <port> <tokens-file>   (needs GROOT_DB and GROOT_WEBAPP in the environment)

Prints GROOT_READY once it is serving. Everything lives in a temporary database file.
"""
import json
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'groot.browser_settings')
sys.path.insert(0, os.getcwd())

import django  # noqa: E402

django.setup()
from django.conf import settings  # noqa: E402

assert settings.DATABASES['default']['ENGINE'].endswith('sqlite3'), 'Groot must only ever use its own throwaway database'

from django.core.management import call_command  # noqa: E402

port, tokens_file = sys.argv[1], sys.argv[2]
call_command('migrate', verbosity=0)

from relationships.models import RelationshipType  # noqa: E402
from users.models import User  # noqa: E402
from users.views import get_tokens_for_user  # noqa: E402

for name in ['Father', 'Mother', 'Son', 'Daughter', 'Husband', 'Wife', 'Spouse', 'Partner', 'Brother', 'Sister',
             'Grandfather', 'Grandmother', 'Grandson', 'Granddaughter', 'Stepfather', 'Stepmother', 'Adopted Son',
             'Adopted Daughter', 'Uncle', 'Aunt', 'Cousin', 'Fiance', 'Fiancee', 'Guardian']:
    RelationshipType.objects.get_or_create(type_name=name)

tokens = {}
for key, first, last, phone in [('owner', 'Olive', 'Owner', '555-0100'), ('member', 'Mia', 'Member', '555-0101'),
                                ('outsider', 'Sam', 'Stranger', '555-0102')]:
    u = User.objects.create_user(email=f'groot-{key}@example.test', google_id=f'groot-{key}', first_name=first, last_name=last)
    u.phone = phone
    u.address = f'{first} test street'
    u.save()
    t = get_tokens_for_user(u)
    tokens[key] = {'access': t['access'], 'refresh': t['refresh'], 'id': u.id, 'name': f'{first} {last}', 'email': u.email}
with open(tokens_file, 'w', encoding='utf-8') as f:
    json.dump(tokens, f)
print('GROOT_READY', flush=True)
call_command('runserver', f'127.0.0.1:{port}', use_reloader=False, verbosity=0)
