import os, json
os.environ['DJANGO_SETTINGS_MODULE'] = 'groot.settings'
import django; django.setup()
from django.core.management import call_command
call_command('migrate', verbosity=0)
from datetime import date, timedelta
from django.utils import timezone
from rest_framework.test import APIClient
from users.models import User
from users.views import get_tokens_for_user
from family_trees.models import FamilyTree, TreeMember
from family_members.models import FamilyMember
from relationships.models import Relationship, RelationshipType
from family_codes.models import FamilyCode
from join_requests.models import JoinRequest

fails = []
def chk(cond, msg):
    print(('PASS ' if cond else 'FAIL ') + msg)
    if not cond: fails.append(msg)

def mk(email, first, **kw):
    u = User.objects.create_user(email=email, google_id='g-' + email, first_name=first, last_name='T', **kw)
    u.phone = '555-' + first; u.address = first + ' street'; u.save()
    return u, APIClient(HTTP_AUTHORIZATION='Bearer ' + get_tokens_for_user(u)['access'])

def tree(owner, name, active=True):
    t = FamilyTree.objects.create(owner=owner, tree_name=name, is_active=active)
    TreeMember.objects.create(tree=t, user=owner, role='owner'); return t

own, O = mk('own@x.com', 'Own'); mem, M = mk('mem@x.com', 'Mem'); out, X = mk('out@x.com', 'Out')
sup, S = mk('sup@x.com', 'Sup', is_staff=True, is_superuser=True)
T = tree(own, 'Main'); TreeMember.objects.create(tree=T, user=mem, role='member')
T2 = tree(out, 'Other')
a = FamilyMember.objects.create(tree=T, first_name='A', last_name='L', created_by=own)
b = FamilyMember.objects.create(tree=T, first_name='B', last_name='L', created_by=own)
c = FamilyMember.objects.create(tree=T, first_name='C', last_name='L', created_by=own)
other = FamilyMember.objects.create(tree=T2, first_name='Z', last_name='L', created_by=out)
if not RelationshipType.objects.exists():
    for n in ['Father', 'Mother', 'Son', 'Husband', 'Wife', 'Brother']:
        RelationshipType.objects.create(type_name=n)
rt = {r.type_name: r.id for r in RelationshipType.objects.all()}

print('== C1 tree field on update')
r = M.patch(f'/api/family-members/{a.id}/', {'tree': T2.id, 'first_name': 'Hacked'}, format='json')
a.refresh_from_db(); chk(r.status_code == 400 and a.tree_id == T.id, 'member PATCH tree -> other tree refused')
r = O.patch(f'/api/family-members/{a.id}/', {'tree': T2.id}, format='json')
a.refresh_from_db(); chk(a.tree_id == T.id, 'even the owner cannot move a person to another tree (and not into one they own)')
rel = Relationship.objects.create(tree=T, member_1=a, member_2=b, relationship_type_id=rt['Brother'], created_by=own)
r = M.patch(f'/api/relationships/{rel.id}/', {'tree': T2.id}, format='json'); rel.refresh_from_db()
chk(rel.tree_id == T.id, 'relationship PATCH tree ignored')
r = M.patch(f'/api/relationships/{rel.id}/', {'member_2': other.id}, format='json'); rel.refresh_from_db()
chk(r.status_code == 400 and rel.member_2_id == b.id, 'relationship PATCH to a person in another tree refused')
r = M.post('/api/family-members/', {'tree': T2.id, 'first_name': 'Plant'}, format='json')
chk(r.status_code == 403 and not FamilyMember.objects.filter(first_name='Plant').exists(), 'cannot plant a person in a tree you are not in')
r = M.post('/api/relationships/', {'tree': T.id, 'member_1': a.id, 'member_2': other.id, 'relationship_type': rt['Father']}, format='json')
chk(r.status_code == 400, 'cannot create a link to a person from another tree')
r = X.post('/api/relationships/', {'tree': T.id, 'member_1': a.id, 'member_2': c.id, 'relationship_type': rt['Father']}, format='json')
chk(r.status_code == 403, 'outsider cannot create links')
# tree id in URL/body mismatch on create
r = M.post('/api/relationships/', {'tree': T2.id, 'member_1': a.id, 'member_2': c.id, 'relationship_type': rt['Father']}, format='json')
chk(r.status_code in (400, 403), 'body tree different from member trees refused')

print('== C2 user field')
r = M.patch(f'/api/family-members/{a.id}/', {'user': out.id}, format='json'); a.refresh_from_db()
chk(r.status_code == 400 and a.user_id is None, 'member cannot link a person to someone else\'s account')
r = M.patch(f'/api/family-members/{a.id}/', {'user': mem.id}, format='json'); a.refresh_from_db()
chk(r.status_code == 400 and a.user_id is None, 'member cannot link a person to THEMSELVES to read a private phone')
r = O.patch(f'/api/family-members/{a.id}/', {'user': out.id}, format='json'); a.refresh_from_db()
chk(r.status_code == 400 and a.user_id is None, 'owner cannot link an account that is not in the tree')
r = O.patch(f'/api/family-members/{a.id}/', {'user': mem.id}, format='json'); a.refresh_from_db()
chk(r.status_code == 200 and a.user_id == mem.id, 'owner can link a tree member')
a.user = None; a.save()
FamilyMember.objects.filter(id=a.id).update(phone='111', phone_public=False)
r = M.get(f'/api/family-members/{a.id}/'); chk(r.json()['phone'] == '', 'private phone hidden from a plain member')
r = M.post('/api/family-members/', {'tree': T.id, 'first_name': 'New', 'user': mem.id}, format='json')
chk(r.status_code == 201 and r.json()['user'] is None, 'create with a self-link just drops the link')

print('== C3 leaks')
txt = lambda r: json.dumps(r.json())
for name, r in [
    ('tree list', M.get('/api/family-trees/')), ('tree detail', M.get(f'/api/family-trees/{T.id}/')),
    ('history', M.get(f'/api/edit-history/?tree_id={T.id}')),
]:
    t = txt(r)
    chk('555-Own' not in t and 'Own street' not in t, f'{name}: no phone/address of other users ({r.status_code})')
r = O.post('/api/family-codes/generate/', {'tree_id': T.id}, format='json'); code = r.json()['code']
chk('555-' not in txt(r), 'generate code response is clean')
r = M.get('/api/users/me/'); chk(r.json()['phone'] == '555-Mem', 'your own profile still shows your own phone')
r = M.get('/api/users/me/'); chk(not r.json()['is_superuser'], 'not superuser')
r = M.patch('/api/users/me/', {'is_superuser': True, 'is_staff': True, 'email': 'new@x.com'}, format='json'); mem.refresh_from_db()
chk(not mem.is_superuser and not mem.is_staff and mem.email == 'mem@x.com', 'cannot self-promote or change email through the profile')

print('== C4 inactive trees')
D = tree(own, 'Gone', active=False)
dm = FamilyMember.objects.create(tree=D, first_name='Ghost', last_name='L', created_by=own)
TreeMember.objects.create(tree=D, user=mem, role='member')
dc = FamilyCode.objects.create(tree=D, code='GONE12', created_by=own)
for label, r in [
    ('members list', M.get(f'/api/family-members/?tree_id={D.id}')), ('member get', M.get(f'/api/family-members/{dm.id}/')),
    ('relationships list', M.get(f'/api/relationships/?tree_id={D.id}')), ('history', M.get(f'/api/edit-history/?tree_id={D.id}')),
    ('tree detail', M.get(f'/api/family-trees/{D.id}/')), ('redeem', X.post('/api/family-codes/redeem/', {'code': 'GONE12'}, format='json')),
    ('join request create', X.post('/api/join-requests/', {'code': 'GONE12'}, format='json')),
    ('member edit', M.patch(f'/api/family-members/{dm.id}/', {'first_name': 'x'}, format='json')),
    ('member create', M.post('/api/family-members/', {'tree': D.id, 'first_name': 'x'}, format='json')),
]:
    chk(r.status_code in (403, 404, 409, 400), f'inactive tree: {label} -> {r.status_code}')
chk(D.id not in [t['id'] for t in M.get('/api/family-trees/').json()], 'inactive tree not in your tree list')

print('== H9 / owner-only delete')
r = M.delete(f'/api/family-members/{c.id}/'); chk(r.status_code == 403 and FamilyMember.objects.filter(id=c.id).exists(), 'member cannot delete a person')
r = M.delete(f'/api/relationships/{rel.id}/'); chk(r.status_code == 403 and Relationship.objects.filter(id=rel.id).exists(), 'member cannot delete a relationship')
r = X.delete(f'/api/family-members/{c.id}/'); chk(r.status_code == 403, 'outsider cannot delete')
r = M.delete(f'/api/family-trees/{T.id}/'); chk(FamilyTree.objects.get(id=T.id).is_active, 'member cannot delete the tree')
r = M.post(f'/api/family-codes/generate/', {'tree_id': T.id}, format='json'); chk(r.status_code == 403, 'member cannot generate codes')
chk(S.get(f'/api/staff/trees/').status_code == 200 and M.get('/api/staff/trees/').status_code == 403 and X.get(f'/api/staff/trees/{T.id}/').status_code == 403, 'staff endpoints: only superuser')
r = O.delete(f'/api/family-members/{c.id}/'); chk(r.status_code == 200, 'owner can delete a leaf person')

print('== C6 code redemption / join approval (sequential double use; row locks reviewed in code)')
T.approval_required = False; T.save()
r1 = X.post('/api/family-codes/redeem/', {'code': code}, format='json')
mm, MM = mk('m2@x.com', 'Two')
r2 = MM.post('/api/family-codes/redeem/', {'code': code}, format='json')
chk(r1.status_code in (200, 201) and r2.status_code == 400, 'single-use code works once only')
T.approval_required = True; T.save()
q, Q = mk('q@x.com', 'Q')
rj = Q.post('/api/join-requests/', {'tree': T.id, 'message': 'hi'}, format='json')
jid = JoinRequest.objects.filter(requester=q).first()
if jid:
    p1 = O.patch(f'/api/join-requests/{jid.id}/', {'status': 'approved'}, format='json')
    p2 = O.patch(f'/api/join-requests/{jid.id}/', {'status': 'approved'}, format='json')
    chk(p1.status_code == 200 and p2.status_code == 400 and TreeMember.objects.filter(tree=T, user=q).count() == 1, 'join request approved only once, one membership')
    p3 = M.patch(f'/api/join-requests/{jid.id}/', {'status': 'rejected'}, format='json'); chk(p3.status_code in (403, 404), 'non-owner cannot decide a request')
else:
    print('SKIP join request create shape differs:', rj.status_code, rj.content[:120])

print('== C7 relationship rules')
x, y = a, b
Relationship.objects.filter(tree=T).delete()
r = O.post('/api/relationships/', {'tree': T.id, 'member_1': x.id, 'member_2': y.id, 'relationship_type': rt['Father']}, format='json'); chk(r.status_code == 201, 'first link')
r = O.post('/api/relationships/', {'tree': T.id, 'member_1': x.id, 'member_2': y.id, 'relationship_type': rt['Husband']}, format='json'); chk(r.status_code == 400, 'father AND husband of the same person refused')
r = O.post('/api/relationships/', {'tree': T.id, 'member_1': y.id, 'member_2': x.id, 'relationship_type': rt['Husband']}, format='json'); chk(r.status_code == 400, '... in the other direction too')
r = O.post('/api/relationships/', {'tree': T.id, 'member_1': y.id, 'member_2': x.id, 'relationship_type': rt['Father']}, format='json'); chk(r.status_code == 400, 'cannot make them each other\'s father')
r = O.post('/api/relationships/', {'tree': T.id, 'member_1': x.id, 'member_2': x.id, 'relationship_type': rt['Father']}, format='json'); chk(r.status_code == 400, 'self-link refused')
cc = FamilyMember.objects.create(tree=T, first_name='Cc', last_name='L', created_by=own)
O.post('/api/relationships/', {'tree': T.id, 'member_1': y.id, 'member_2': cc.id, 'relationship_type': rt['Father']}, format='json')
r = O.post('/api/relationships/', {'tree': T.id, 'member_1': cc.id, 'member_2': x.id, 'relationship_type': rt['Father']}, format='json'); chk(r.status_code == 400, 'grandchild cannot become grandparent (loop)')

print('== dates')
r = O.patch(f'/api/family-members/{a.id}/', {'birth_date': str(timezone.localdate() + timedelta(days=2))}, format='json'); chk(r.status_code == 400, 'future birth date refused')
r = O.patch(f'/api/family-members/{a.id}/', {'death_date': str(timezone.localdate() + timedelta(days=2))}, format='json'); chk(r.status_code == 400, 'future death date refused')
r = O.patch(f'/api/family-members/{a.id}/', {'birth_date': '2000-01-01', 'death_date': '1990-01-01'}, format='json'); chk(r.status_code == 400, 'death before birth refused')
r = O.post('/api/family-members/', {'tree': T.id, 'first_name': 'F', 'birth_date': str(timezone.localdate() + timedelta(days=30))}, format='json'); chk(r.status_code == 400, 'create with future birth date refused')
r = O.patch(f'/api/family-members/{a.id}/', {'birth_date': str(date.today())}, format='json'); chk(r.status_code == 200, 'today is fine')

print('\nFAILURES:', fails or 'none')
print('== RERUN: code redemption on an open tree, future dates vs server date')
from django.utils import timezone
T3 = tree(own, 'Open'); T3.approval_required = False; T3.save()
code3 = O.post('/api/family-codes/generate/', {'tree_id': T3.id}, format='json').json()['code']
u1, U1 = mk('u1@x.com', 'U1'); u2, U2 = mk('u2@x.com', 'U2')
ra = U1.post('/api/family-codes/redeem/', {'code': code3}, format='json'); rb = U2.post('/api/family-codes/redeem/', {'code': code3}, format='json')
print(ra.status_code, rb.status_code)
chk(ra.status_code in (200, 201) and rb.status_code == 400 and TreeMember.objects.filter(tree=T3).count() == 2, 'single-use code redeems once; second user refused; exactly one new member')
chk(U1.post('/api/family-codes/redeem/', {'code': code3}, format='json').status_code == 400, 'same person redeeming again refused')
T3.approval_required = True; T3.save()
jr = U2.post('/api/join-requests/', {'code': 'NOPE'}, format='json'); print('bad code join:', jr.status_code)
tomorrow = timezone.localdate() + timedelta(days=1)
r = O.patch(f'/api/family-members/{a.id}/', {'birth_date': str(tomorrow + timedelta(days=1))}, format='json'); chk(r.status_code == 400, 'birth date beyond tomorrow refused')
r = O.patch(f'/api/family-members/{a.id}/', {'death_date': str(tomorrow + timedelta(days=1)), 'birth_date': '1990-01-01'}, format='json'); chk(r.status_code == 400, 'death date beyond tomorrow refused')
print('FAILURES2:', fails)
print('== RERUN: join request approval')
T4 = tree(own, 'Approval'); T4.approval_required = True; T4.save()
code4 = O.post('/api/family-codes/generate/', {'tree_id': T4.id}, format='json').json()['code']
w, W = mk('w@x.com', 'W')
r = W.post('/api/join-requests/', {'code': code4, 'message': 'hi'}, format='json'); print(r.status_code, r.content[:150])
j = JoinRequest.objects.filter(requester=w).first()
chk(j is not None and not TreeMember.objects.filter(tree=T4, user=w).exists(), 'request pending, no access yet')
r0 = W.get(f'/api/family-members/?tree_id={T4.id}'); chk(r0.status_code == 403, 'requester cannot read the tree while pending')
chk(M.patch(f'/api/join-requests/{j.id}/', {'status': 'approved'}, format='json').status_code in (403, 404), 'non-owner cannot approve')
chk(W.patch(f'/api/join-requests/{j.id}/', {'status': 'approved'}, format='json').status_code in (403, 404), 'requester cannot approve themselves')
p1 = O.patch(f'/api/join-requests/{j.id}/', {'status': 'approved'}, format='json'); p2 = O.patch(f'/api/join-requests/{j.id}/', {'status': 'approved'}, format='json')
chk(p1.status_code == 200 and p2.status_code == 400 and TreeMember.objects.filter(tree=T4, user=w).count() == 1, 'approved once, single membership')
print('FAILURES3:', fails)
