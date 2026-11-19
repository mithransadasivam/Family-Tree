import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'qa.settings'
import django; django.setup()
from django.core.management import call_command
call_command('migrate', verbosity=0)
from rest_framework.test import APIClient
from users.models import User
from users.views import get_tokens_for_user
from family_trees.models import FamilyTree, TreeMember
from communities.models import CommunityTree, CommunityMember
chk = lambda c, m: print(('PASS ' if c else 'FAIL ') + m) or (c or exit(1))
def mk(e, f):
    u = User.objects.create_user(email=e, google_id='g-' + e, first_name=f, last_name='T')
    return u, APIClient(HTTP_AUTHORIZATION='Bearer ' + get_tokens_for_user(u)['access'])
o, O = mk('o@x.com', 'Olive'); b, B = mk('b@x.com', 'Bob'); c, C = mk('c@x.com', 'Cat')
cid = O.post('/api/communities/', {'name': 'Village'}, format='json').json()['id']
t = FamilyTree.objects.create(owner=b, tree_name='Bob Family'); TreeMember.objects.create(tree=t, user=b, role='owner')
ot = FamilyTree.objects.create(owner=o, tree_name='Olive Family'); TreeMember.objects.create(tree=ot, user=o, role='owner')
r = B.post(f'/api/communities/{cid}/join/', {'tree_id': ot.id}, format='json')
chk(r.status_code == 403, "can't offer someone else's tree")
r = B.post(f'/api/communities/{cid}/join/', {'tree_id': t.id}, format='json'); chk(r.status_code == 201, 'join with own tree')
chk(CommunityTree.objects.count() == 0, 'nothing shared before approval')
reqs = O.get(f'/api/communities/{cid}/requests/').json(); chk(reqs[0]['tree_name'] == 'Bob Family', 'owner sees offered family in list')
d = O.get(f'/api/community-requests/{reqs[0]["id"]}/').json(); chk(d['tree_name'] == 'Bob Family', 'and on the approve page')
O.patch(f'/api/community-requests/{reqs[0]["id"]}/', {'status': 'approved'}, format='json')
chk(CommunityTree.objects.filter(community_id=cid, tree=t).exists() and CommunityMember.objects.filter(community_id=cid, user=b).exists(), 'approval adds member and shares the chosen tree')
r = C.post(f'/api/communities/{cid}/join/', {}, format='json'); chk(r.status_code == 201, 'join without a tree still works')
rid = O.get(f'/api/communities/{cid}/requests/').json()[0]['id']
O.patch(f'/api/community-requests/{rid}/', {'status': 'approved'}, format='json')
chk(CommunityTree.objects.count() == 1, 'no extra tree shared for the no-tree join')
print('ALL PASSED')
