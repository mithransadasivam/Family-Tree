import os, json
os.environ['DJANGO_SETTINGS_MODULE'] = 'groot.settings'
import django; django.setup()
from django.core.management import call_command
call_command('migrate', verbosity=0)
from rest_framework.test import APIClient
from users.models import User
from users.views import get_tokens_for_user
from family_trees.models import FamilyTree, TreeMember
from family_members.models import FamilyMember
fails = []
def chk(c, m):
    print(('PASS ' if c else 'FAIL ') + m)
    if not c: fails.append(m)
def mk(e, f, **kw):
    u = User.objects.create_user(email=e, google_id='g' + e, first_name=f, last_name='T', **kw)
    u.phone = '555-' + f; u.address = f + ' Street'; u.save()
    return u, APIClient(HTTP_AUTHORIZATION='Bearer ' + get_tokens_for_user(u)['access'])
o, O = mk('own@x.com', 'Own'); m, M = mk('mem@x.com', 'Mem'); s, S = mk('sup@x.com', 'Sup', is_staff=True, is_superuser=True)
T = FamilyTree.objects.create(owner=o, tree_name='T'); TreeMember.objects.create(tree=T, user=o, role='owner'); TreeMember.objects.create(tree=T, user=m, role='member')

print('== accounts')
t = M.get(f'/api/family-trees/{T.id}/').json()
chk(t['owner']['email'] == '' and t['owner']['phone'] == '' and t['owner']['address'] == '', 'owner\'s email/phone/address hidden from a member by default')
chk(M.get('/api/users/me/').json()['email'] == 'mem@x.com', 'you still see your own email')
r = O.patch('/api/users/me/', {'email_public': True}, format='json'); chk(r.status_code == 200 and r.json()['email_public'] is True, 'eye on for email saves')
t = M.get(f'/api/family-trees/{T.id}/').json()
chk(t['owner']['email'] == 'own@x.com' and t['owner']['phone'] == '', 'email now visible, phone/address still hidden')
O.patch('/api/users/me/', {'phone_public': True, 'address_public': True}, format='json')
t = M.get(f'/api/family-trees/{T.id}/').json(); chk(t['owner']['phone'] == '555-Own' and t['owner']['address'] == 'Own Street', 'phone & address visible once their eyes are on')
O.patch('/api/users/me/', {'email_public': False}, format='json')
chk(M.get(f'/api/family-trees/{T.id}/').json()['owner']['email'] == '', 'eye off hides it again')
hist = M.get(f'/api/edit-history/?tree_id={T.id}').json(); chk('own@x.com' not in json.dumps(hist), 'history does not leak the email')
sl = S.get('/api/staff/trees/').json(); sl = sl.get('results', sl); chk(any(x['owner']['email'] == 'own@x.com' for x in sl), 'staff pages still see the owner email')

print('== people')
p = FamilyMember.objects.create(tree=T, first_name='P', last_name='L', created_by=o, email='p@x.com', address='1 Main', phone='123')
g = M.get(f'/api/family-members/{p.id}/').json()
chk(g['email'] == '' and g['address'] == '' and g['phone'] == '', 'private email/address/phone blank for a member')
g = O.get(f'/api/family-members/{p.id}/').json(); chk(g['email'] == 'p@x.com' and g['address'] == '1 Main', 'owner sees all')
r = M.patch(f'/api/family-members/{p.id}/', {'email': 'evil@x.com', 'address_public': True, 'first_name': 'Px'}, format='json'); p.refresh_from_db()
chk(r.status_code == 200 and p.email == 'p@x.com' and not p.address_public and p.first_name == 'Px', 'member cannot overwrite or open up private details')
r = O.patch(f'/api/family-members/{p.id}/', {'email_public': True}, format='json')
g = M.get(f'/api/family-members/{p.id}/').json(); chk(g['email'] == 'p@x.com' and g['address'] == '', 'owner opens the email only')
h = O.get(f'/api/edit-history/?tree_id={T.id}').json(); chk('p@x.com' not in json.dumps(h) and '1 Main' not in json.dumps(h), 'history never holds email/address')
print('FAILURES:', fails or 'none')
