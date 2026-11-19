import os, time
os.environ['DJANGO_SETTINGS_MODULE'] = 'groot.settings'
import django; django.setup()
from unittest import mock
from django.conf import settings
from django.core import mail
from django.core.management import call_command
call_command('migrate', verbosity=0)
from rest_framework.test import APIClient
from users.models import User
from users.views import get_tokens_for_user
from family_trees.models import FamilyTree, TreeMember
from family_codes.models import FamilyCode
from communities.models import CommunityJoinRequest
from django.utils import timezone
from datetime import timedelta

chk = lambda cond, msg: print(('PASS ' if cond else 'FAIL ') + msg) or (cond or exit(1))
def mk(email, first):
    u = User.objects.create_user(email=email, google_id='g-' + email, first_name=first, last_name='T')
    return u, APIClient(HTTP_AUTHORIZATION='Bearer ' + get_tokens_for_user(u)['access'])
def settle():  # emails go out on a background thread
    for _ in range(40):
        time.sleep(0.05)
    return len(mail.outbox)

owner, O = mk('owner@x.com', 'Olive'); bob, B = mk('bob@x.com', 'Bob'); cat, C = mk('cat@x.com', 'Cat')
settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
settings.SITE_URL = 'https://kinship.example'

# --- community
cid = O.post('/api/communities/', {'name': 'Riverside\nVillage'}, format='json').json()['id']
r = B.post(f'/api/communities/{cid}/join/', {'message': 'I live on River Road'}, format='json')
chk(r.status_code == 201, 'join request accepted')
settle(); chk(len(mail.outbox) == 1 and mail.outbox[0].to == ['owner@x.com'], 'the community owner got exactly one email')
m = mail.outbox[0]
rid = CommunityJoinRequest.objects.get().id
chk('\n' not in m.subject and 'Bob T wants to join' in m.subject, f'subject is one clean line: {m.subject!r}')
chk(f'https://kinship.example/approve/community/{rid}' in m.body and 'bob@x.com' in m.body and 'River Road' in m.body, 'body names the person, quotes their message, links to the approve page')
chk('approve=' not in m.body and 'token' not in m.body.lower(), 'the link carries no secret: approving still needs the owner signed in')
# detail endpoint: owner only
d = O.get(f'/api/community-requests/{rid}/'); chk(d.status_code == 200 and d.json()['target_name'].startswith('Riverside') and d.json()['status'] == 'pending', 'owner can open the request')
chk(B.get(f'/api/community-requests/{rid}/').status_code == 404 and C.get(f'/api/community-requests/{rid}/').status_code == 404, 'the requester and strangers get 404')
chk(APIClient().get(f'/api/community-requests/{rid}/').status_code == 401, 'anonymous gets 401')
chk(O.patch(f'/api/community-requests/{rid}/', {'status': 'approved'}, format='json').status_code == 200, 'owner approves from the same page')

# --- decline then re-ask: cooldown
mail.outbox.clear()
C.post(f'/api/communities/{cid}/join/', {}, format='json'); rid2 = CommunityJoinRequest.objects.filter(requester=cat).get().id
O.patch(f'/api/community-requests/{rid2}/', {'status': 'rejected'}, format='json')
r = C.post(f'/api/communities/{cid}/join/', {}, format='json'); chk(r.status_code == 400 and 'tomorrow' in r.json()['error'], 'after a decline you cannot immediately re-ask')
CommunityJoinRequest.objects.filter(id=rid2).update(created_at=timezone.now() - timedelta(days=2))
chk(C.post(f'/api/communities/{cid}/join/', {}, format='json').status_code == 201, 'a day later you can ask again')

# --- mail failure must never break the request
mail.outbox.clear()
dave, D = mk('dave@x.com', 'Dave')
with mock.patch('utils.notify.send_mail', side_effect=RuntimeError('smtp down')):
    r = D.post(f'/api/communities/{cid}/join/', {}, format='json'); settle()
chk(r.status_code == 201, 'SMTP outage: the join request still succeeds')

# --- email not configured: silently skipped
settings.EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'
mail.outbox.clear(); erin, E = mk('erin@x.com', 'Erin')
r = E.post(f'/api/communities/{cid}/join/', {}, format='json'); settle()
chk(r.status_code == 201 and len(mail.outbox) == 0, 'no email set-up: request works, nothing sent, no crash')
settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# --- family tree join by code
mail.outbox.clear()
t = FamilyTree.objects.create(owner=owner, tree_name='Smith Family Tree', approval_required=True); TreeMember.objects.create(tree=t, user=owner, role='owner')
FamilyCode.objects.create(tree=t, code='ABC123', created_by=owner)
r = B.post('/api/join-requests/', {'code': 'ABC123', 'message': 'hi'}, format='json'); chk(r.status_code == 201 and r.json()['auto_approved'] is False, 'tree join request created (approval required)')
settle(); chk(len(mail.outbox) == 1 and mail.outbox[0].to == ['owner@x.com'], 'the tree owner got an email')
from join_requests.models import JoinRequest
jid = JoinRequest.objects.get().id
chk(f'https://kinship.example/approve/tree/{jid}' in mail.outbox[0].body, 'tree email links to the approve page')
chk(O.get(f'/api/join-requests/{jid}/').json()['kind'] == 'tree' and B.get(f'/api/join-requests/{jid}/').status_code == 404, 'tree request detail: owner only')
# auto-approved trees send nothing
t2 = FamilyTree.objects.create(owner=owner, tree_name='Open', approval_required=False); TreeMember.objects.create(tree=t2, user=owner, role='owner')
FamilyCode.objects.create(tree=t2, code='OPEN12', created_by=owner); mail.outbox.clear()
C.post('/api/join-requests/', {'code': 'OPEN12'}, format='json'); settle()
chk(len(mail.outbox) == 0, 'auto-approved joins do not email')
print('ALL PASSED')
