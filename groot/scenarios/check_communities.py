import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'groot.settings'
import django; django.setup()
from datetime import date
from django.core.management import call_command
call_command('migrate', verbosity=0)
from rest_framework.test import APIClient
from users.models import User
from users.views import get_tokens_for_user
from family_trees.models import FamilyTree, TreeMember
from family_members.models import FamilyMember
from relationships.models import Relationship, RelationshipType
from django.core.cache import cache
cache.clear()

chk = lambda cond, msg: print(('PASS ' if cond else 'FAIL ') + msg) or (cond or exit(1))

def mk(email, first):
    u = User.objects.create_user(email=email, google_id='g-' + email, first_name=first, last_name='T')
    return u, APIClient(HTTP_AUTHORIZATION='Bearer ' + get_tokens_for_user(u)['access'])

today = date.today()
def born(age, extra_days=0):
    # someone whose age today is exactly `age`
    try: d = today.replace(year=today.year - age)
    except ValueError: d = today.replace(year=today.year - age, day=28)
    return d

owner, O = mk('owner@x.com', 'Olive'); bob, B = mk('bob@x.com', 'Bob'); cat, C = mk('cat@x.com', 'Cat'); eve, E = mk('eve@x.com', 'Eve')
anon = APIClient()

def tree(user, name):
    t = FamilyTree.objects.create(owner=user, tree_name=name); TreeMember.objects.create(tree=t, user=user, role='owner'); return t
def person(t, first, last='Pell', **kw): return FamilyMember.objects.create(tree=t, first_name=first, last_name=last, created_by=t.owner, **kw)

# ---------- phone privacy in family trees
t1 = tree(owner, 'Owner family'); TreeMember.objects.create(tree=t1, user=bob, role='member')
p = person(t1, 'Priv', phone='111', phone_public=False)
q = person(t1, 'Pub', phone='222', phone_public=True)
rows = {r['first_name']: r for r in O.get(f'/api/family-members/?tree_id={t1.id}').json()}
chk(rows['Priv']['phone'] == '111' and rows['Pub']['phone'] == '222', 'tree owner sees private and public numbers')
rows = {r['first_name']: r for r in B.get(f'/api/family-members/?tree_id={t1.id}').json()}
chk(rows['Priv']['phone'] == '' and rows['Pub']['phone'] == '222' and rows['Priv']['phone_public'] is False, 'other tree member: private blank, public visible')
chk(B.get(f'/api/family-members/{p.id}/').json()['phone'] == '', 'single-member read also hides a private number')
r = B.patch(f'/api/family-members/{p.id}/', {'first_name': 'Priv2', 'phone': '999', 'phone_public': True}, format='json')
p.refresh_from_db()
chk(r.status_code == 200 and p.first_name == 'Priv2' and p.phone == '111' and p.phone_public is False, 'non-owner edit changes the name but cannot overwrite a private number or make it public')
chk(O.patch(f'/api/family-members/{p.id}/', {'phone_public': True}, format='json').json()['phone_public'] is True, 'owner can make it public')
O.patch(f'/api/family-members/{p.id}/', {'phone_public': False}, format='json')
p.user = bob; p.save()
chk(B.get(f'/api/family-members/{p.id}/').json()['phone'] == '111', 'the person themself (linked account) sees their private number')
p.user = None; p.save()
r = B.post('/api/family-members/', {'tree': t1.id, 'first_name': 'New', 'phone': '555'}, format='json'); chk(r.status_code == 201 and r.json()['phone_public'] is False, 'new people default to a private number')

# ---------- communities: create / find / join
r = O.post('/api/communities/', {'name': 'Riverside Village', 'description': 'our village'}, format='json'); chk(r.status_code == 201 and r.json()['role'] == 'owner', 'create a community (creator becomes owner)')
cid = r.json()['id']
chk(O.post('/api/communities/', {'name': 'x'}, format='json').status_code == 400, 'too-short name refused')
chk(B.get('/api/communities/find/?q=r').json() == [], 'find needs at least 2 characters')
f = B.get('/api/communities/find/?q=riverside').json(); chk(len(f) == 1 and f[0]['status'] is None and 'owner' not in f[0], 'find by name works and reveals no owner details')
chk(B.get(f'/api/communities/{cid}/').status_code == 404, 'non-member cannot open community details')
chk(B.get(f'/api/communities/{cid}/people/').status_code == 404, 'non-member cannot search its people')
chk(B.post(f'/api/communities/{cid}/join/', {}, format='json').status_code == 201, 'request to join')
chk(B.post(f'/api/communities/{cid}/join/', {}, format='json').status_code == 400, 'duplicate request refused')
chk(B.get('/api/communities/find/?q=riverside').json()[0]['status'] == 'pending', 'find shows pending')
chk(B.get(f'/api/communities/{cid}/people/').status_code == 404, 'pending is still not a member')
reqs = O.get(f'/api/communities/{cid}/requests/').json(); chk(len(reqs) == 1 and reqs[0]['email'] == 'bob@x.com', 'owner sees the request')
chk(B.get(f'/api/communities/{cid}/requests/').status_code in (403, 404), 'requester cannot list requests')
chk(C.patch(f'/api/community-requests/{reqs[0]["id"]}/', {'status': 'approved'}, format='json').status_code == 404, 'a stranger cannot approve')
chk(O.patch(f'/api/community-requests/{reqs[0]["id"]}/', {'status': 'approved'}, format='json').status_code == 200, 'owner approves')
chk(B.get(f'/api/communities/{cid}/').json()['role'] == 'member', 'approved user is a member')
chk(O.patch(f'/api/community-requests/{reqs[0]["id"]}/', {'status': 'rejected'}, format='json').status_code == 400, 'a handled request cannot be handled again')
C.post(f'/api/communities/{cid}/join/', {}, format='json'); rid = O.get(f'/api/communities/{cid}/requests/').json()[0]['id']
O.patch(f'/api/community-requests/{rid}/', {'status': 'rejected'}, format='json')
chk(C.get(f'/api/communities/{cid}/').status_code == 404, 'a rejected user is not a member')

# ---------- sharing + search
people = [
    ('Alan', 'Pell', dict(gender='male', birth_date=born(25), phone='700', phone_public=True)),
    ('Anna', 'Pell', dict(gender='female', birth_date=born(25), phone='701', phone_public=False)),
    ('Ben', 'Okafor', dict(gender='male', birth_date=born(40))),
    ('Cara', 'Okafor', dict(gender='female', birth_date=born(30))),
    ('Dev', 'Okafor', dict(gender='', birth_date=born(26))),            # gender inferred from a relationship
    ('Old', 'Timer', dict(gender='male', birth_date=date(1930, 5, 5), death_date=date(2001, 1, 1))),
    ('NoDob', 'Pell', dict(gender='male')),
]
mem = {fn: person(t1, fn, ln, **kw) for fn, ln, kw in people}
mem['Alan'].address = '1 Secret Street'; mem['Alan'].photo_url = 'https://x/y.png'; mem['Alan'].email = 'alan@x.com'; mem['Alan'].save()
husband = RelationshipType.objects.create(type_name='Husband', category='marriage')
Relationship.objects.create(tree=t1, member_1=mem['Dev'], member_2=mem['Cara'], relationship_type=husband, created_by=owner)
t2 = tree(bob, 'Bob family'); person(t2, 'Zed', 'Bobson', gender='male', birth_date=born(25))
t_hidden = tree(owner, 'Never shared'); person(t_hidden, 'Hidden', 'Person', gender='male', birth_date=born(25))

def search(client, **params):
    from urllib.parse import urlencode
    r = client.get(f'/api/communities/{cid}/people/?' + urlencode(params)); chk(r.status_code == 200, f'search {params} -> 200 ({r.status_code})'); return r.json()
chk(search(O)['count'] == 0, 'nothing is searchable until a tree is shared')
chk(O.post(f'/api/communities/{cid}/trees/', {'tree_id': t2.id}, format='json').status_code == 403, "cannot share a tree you do not own (Bob's tree)")
chk(O.post(f'/api/communities/{cid}/trees/', {'tree_id': t1.id}, format='json').status_code == 201, 'owner shares their tree')
chk(C.post(f'/api/communities/{cid}/trees/', {'tree_id': t1.id}, format='json').status_code == 404, 'non-member cannot share into it')
chk(B.post(f'/api/communities/{cid}/trees/', {'tree_id': t2.id}, format='json').status_code == 201, 'member shares their own tree')
names = lambda d: sorted(x['first_name'] for x in d['results'])
res = search(B)
chk('Hidden' not in names(res) and 'Zed' in names(res) and 'Alan' in names(res), 'only shared trees appear; unshared tree people never do')
keys = set(next(x for x in res['results'] if x['first_name'] == 'Alan').keys())
chk(keys == {'id', 'first_name', 'last_name', 'gender', 'age', 'deceased', 'phone'}, f'result card has only basic fields {sorted(keys)}')
chk('1 Secret Street' not in str(res) and 'alan@x.com' not in str(res) and 'y.png' not in str(res), 'no address, email or photo anywhere in results')
by = {x['first_name']: x for x in res['results']}
chk(by['Alan']['phone'] == '700' and by['Anna']['phone'] == '', 'public number shown, private number never shown')
chk(by['Alan']['age'] == 25 and by['Old']['age'] is None and by['Old']['deceased'] is True, 'age computed; deceased have no age')
chk(names(search(B, gender='male', age=25)) == ['Alan', 'Hidden'.replace('Hidden', 'Zed')] or names(search(B, gender='male', age=25)) == ['Alan', 'Zed'], 'filter: Men, age 25')
chk(names(search(B, gender='female', age=25)) == ['Anna'], 'filter: Women, age 25')
chk(names(search(B, gender='male', age_min=30)) == ['Ben'], 'filter: Men 30 and over (deceased and no-dob excluded)')
chk(names(search(B, age_min=26, age_max=30)) == ['Cara', 'Dev'], 'filter: age range 26-30')
chk('Dev' in names(search(B, gender='male')), 'gender inferred from a relationship (Dev is a Husband)')
chk(names(search(B, living='no')) == ['Old'], 'filter: deceased only')
chk('Old' not in names(search(B, living='yes')), 'filter: living only')
chk(names(search(B, q='okafor')) == ['Ben', 'Cara', 'Dev'], 'name search by last name')
chk(names(search(B, q='ben oka')) == ['Ben'], 'name search by multiple words')
total = FamilyMember.objects.filter(tree__in=[t1, t2]).count()
chk(search(B, limit=2)['count'] == total and len(search(B, limit=2)['results']) == 2 and len(search(B, limit=2, offset=total - 1)['results']) == 1, 'pagination')
for bad in ({'age': 'abc'}, {'age_min': 40, 'age_max': 30}, {'age': 999}):
    from urllib.parse import urlencode
    chk(B.get(f'/api/communities/{cid}/people/?' + urlencode(bad)).status_code == 400, f'bad filter {bad} -> 400')
chk(anon.get(f'/api/communities/{cid}/people/').status_code == 401 and anon.get('/api/communities/').status_code == 401, 'anonymous refused')
chk(E.get(f'/api/communities/{cid}/people/').status_code == 404, 'an unrelated account gets nothing')

# ---------- unsharing / leaving / removing / deleting
chk(C.delete(f'/api/communities/{cid}/trees/{t1.id}/').status_code == 404, 'non-member cannot unshare')
chk(B.delete(f'/api/communities/{cid}/trees/{t1.id}/').status_code == 403, "a member cannot unshare someone else's tree")
chk(B.delete(f'/api/communities/{cid}/trees/{t2.id}/').status_code == 204 and 'Zed' not in names(search(B)), 'owner of a tree stops sharing it')
B.post(f'/api/communities/{cid}/trees/', {'tree_id': t2.id}, format='json')
chk(O.get(f'/api/communities/{cid}/members/').status_code == 200 and B.get(f'/api/communities/{cid}/members/').status_code == 403, 'only the owner lists members')
chk(B.delete(f'/api/communities/{cid}/members/{owner.id}/').status_code == 403, 'a member cannot remove anyone')
chk(O.post(f'/api/communities/{cid}/leave/', {}, format='json').status_code == 400, 'owner cannot leave')
chk(B.post(f'/api/communities/{cid}/leave/', {}, format='json').status_code == 204, 'a member leaves')
chk(B.get(f'/api/communities/{cid}/').status_code == 404 and 'Zed' not in names(search(O)), "leaving removes access and unshares the leaver's trees")
B.post(f'/api/communities/{cid}/join/', {}, format='json'); O.patch(f'/api/community-requests/{O.get(f"/api/communities/{cid}/requests/").json()[0]["id"]}/', {'status': 'approved'}, format='json')
chk(O.delete(f'/api/communities/{cid}/members/{bob.id}/').status_code == 204 and B.get(f'/api/communities/{cid}/').status_code == 404, 'owner removes a member')
chk(B.delete(f'/api/communities/{cid}/').status_code == 404, 'non-member cannot delete')
chk(O.patch(f'/api/communities/{cid}/', {'name': 'Riverside Village 2'}, format='json').json()['name'] == 'Riverside Village 2', 'owner renames')
chk(FamilyMember.objects.filter(tree=t1).count() > 5, 'family tree data untouched by community actions')
chk(O.delete(f'/api/communities/{cid}/').status_code == 204 and O.get(f'/api/communities/{cid}/').status_code == 404, 'owner deletes the community')
chk(FamilyTree.objects.filter(id=t1.id).exists() and FamilyMember.objects.filter(tree=t1).count() > 5, 'deleting a community never deletes family trees or people')
print('ALL PASSED')
