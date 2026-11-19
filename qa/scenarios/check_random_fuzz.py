"""
Random fuzzer: hammers the real API with thousands of odd requests from several users and, as it
goes, checks rules that must ALWAYS hold. Each run uses a new random seed (printed), so running it
again explores different situations; QA_SEED=<n> replays one exactly.

What it checks:
  * the server never answers 5xx, whatever nonsense it is sent
  * no relationship ever joins people from different families, a pair never has two links, and
    parent links never loop
  * a person's private phone/email/address, and an account's, never show up in a response for
    someone who may not see it (a sentinel value is hunted for in every response)
  * strangers are always turned away from a family's data; deleted families vanish
  * community members, shared families and owners stay consistent
"""
import json
import os
import random
import traceback

import django

django.setup()
from django.core.management import call_command  # noqa: E402

call_command('migrate', verbosity=0)

from rest_framework.test import APIClient  # noqa: E402
from communities.models import Community, CommunityJoinRequest, CommunityMember, CommunityTree  # noqa: E402
from family_codes.models import FamilyCode  # noqa: E402
from family_members.models import FamilyMember  # noqa: E402
from family_trees.models import FamilyTree, TreeMember  # noqa: E402
from join_requests.models import JoinRequest  # noqa: E402
from relationships.models import Relationship, RelationshipType  # noqa: E402
from relationships.rules import ancestor_edge  # noqa: E402
from users.models import User  # noqa: E402
from users.views import get_tokens_for_user  # noqa: E402

SEED = int(os.environ.get('QA_SEED') or random.SystemRandom().randrange(1, 10**9))
ROUNDS = int(os.environ.get('QA_ROUNDS') or 600)
rng = random.Random(SEED)

failures, op_log = [], []


def fail(msg):
    failures.append(msg)


TYPE_NAMES = ['Father', 'Mother', 'Son', 'Daughter', 'Husband', 'Wife', 'Spouse', 'Partner', 'Brother', 'Sister',
              'Grandfather', 'Grandmother', 'Grandson', 'Granddaughter', 'Stepfather', 'Adopted Son', 'Uncle',
              'Aunt', 'Cousin', 'Fiance', 'Guardian']
for n in TYPE_NAMES:
    RelationshipType.objects.get_or_create(type_name=n)
TYPES = list(RelationshipType.objects.values_list('id', flat=True))

# ---------------------------------------------------------------- people
users, clients = [], {}
for i in range(6):
    u = User.objects.create_user(email=f'fz{i}@example.com', google_id=f'fz-{i}', first_name=f'U{i}', last_name='Fuzz',
                                 is_staff=(i == 5), is_superuser=(i == 5))
    u.phone, u.address = f'PH-U{i}-SECRET', f'AD-U{i}-SECRET'
    u.save()
    users.append(u)
    clients[u.id] = APIClient(HTTP_AUTHORIZATION='Bearer ' + get_tokens_for_user(u)['access'])
anon = APIClient()
USER_IDS = [u.id for u in users]


def private_values(m):
    """Give a person private details that are easy to spot in any response."""
    m.phone, m.email, m.address = f'PH-M{m.id}~', f'm{m.id}-priv@example.com', f'AD-M{m.id}-SECRET'
    m.save()


def mk_tree(owner, name):
    t = FamilyTree.objects.create(owner=owner, tree_name=name, approval_required=rng.random() < 0.5)
    TreeMember.objects.create(tree=t, user=owner, role='owner')
    for _ in range(rng.randint(2, 4)):
        m = FamilyMember.objects.create(tree=t, first_name=rng.choice(['Ann', 'Bo', 'Cy', 'Di', 'Ed', 'Fay']),
                                        last_name='Fz', created_by=owner,
                                        gender=rng.choice(['male', 'female', '', 'other']))
        private_values(m)
    return t


for i in range(3):
    mk_tree(users[i], f'Tree{i}')
for u in users[3:5]:
    TreeMember.objects.get_or_create(tree=FamilyTree.objects.first(), user=u, defaults={'role': 'member'})


# ---------------------------------------------------------------- helpers
def ids(model, **flt):
    return list(model.objects.filter(**flt).values_list('id', flat=True))


def pick(pool, extra=(99999, 0, -1)):
    """Usually a real id, sometimes a nonexistent one."""
    if not pool or rng.random() < 0.08:
        return rng.choice(extra)
    return rng.choice(pool)


JUNK = [None, '', ' ', 'x' * 400, 12345, -1, 'abc', True, False, [], {}, '2999-01-01', '1900-01-01', 'not a date',
        '😀<script>alert(1)</script>', "Robert'); DROP TABLE users;--", '2000-02-30']


def junk_or(value, p=0.12):
    return rng.choice(JUNK) if rng.random() < p else value


def actor():
    return rng.choice(users + [None])


def call(u, method, path, data=None):
    client = anon if u is None else clients[u.id]
    label = f'{"anon" if u is None else "u" + str(u.id)} {method.upper()} {path} {json.dumps(data, default=str)[:160] if data else ""}'
    op_log.append(label)
    del op_log[:-12]
    try:
        r = getattr(client, method)(path) if (data is None or method == 'get') else getattr(client, method)(path, data, format='json')
    except Exception:  # noqa: BLE001
        fail(f'CRASH on {label}\n{chr(10).join(traceback.format_exc().splitlines()[-9:])}')
        return None
    if r.status_code >= 500:
        fail(f'SERVER ERROR {r.status_code} on {label}: {r.content[:200]!r}')
    return r


def rand_member_payload(tree_id, full=True):
    d = {
        'tree': junk_or(tree_id),
        'first_name': junk_or(rng.choice(['Zed', 'Yan', 'Xi', 'Wu'])),
        'last_name': junk_or('Fz'),
        'gender': junk_or(rng.choice(['male', 'female', 'other', ''])),
        'birth_date': junk_or(rng.choice([None, '1950-05-05', '2001-01-01', '1999-12-31'])),
        'death_date': junk_or(rng.choice([None, None, '2010-01-01', '1940-01-01'])),
        'phone': junk_or('PH-NEW'),
        'phone_public': junk_or(rng.random() < 0.5),
        'email': junk_or('new@example.com'),
        'email_public': junk_or(rng.random() < 0.5),
        'address': junk_or('AD-NEW'),
        'address_public': junk_or(rng.random() < 0.5),
        'user': junk_or(rng.choice(USER_IDS + [None])),
        'birth_place': junk_or('Town'),
    }
    if not full:
        for k in rng.sample(list(d), rng.randint(1, len(d) - 1)):
            del d[k]
    return d


# ---------------------------------------------------------------- operations
def op_create_member():
    u = actor(); tid = pick(ids(FamilyTree))
    r = call(u, 'post', '/api/family-members/', rand_member_payload(tid))
    if r is not None and r.status_code == 201:
        FamilyMember.objects.filter(id=r.json()['id']).update(phone=f'PH-M{r.json()["id"]}~', email=f'm{r.json()["id"]}-priv@example.com', address=f'AD-M{r.json()["id"]}-SECRET')


def op_patch_member():
    call(actor(), 'patch', f'/api/family-members/{pick(ids(FamilyMember))}/', rand_member_payload(pick(ids(FamilyTree)), full=False))


def op_delete_member():
    call(actor(), 'delete', f'/api/family-members/{pick(ids(FamilyMember))}/')


def op_create_rel():
    pool = ids(FamilyMember)
    t = pick(ids(FamilyTree))
    call(actor(), 'post', '/api/relationships/', {
        'tree': junk_or(t), 'member_1': junk_or(pick(pool)), 'member_2': junk_or(pick(pool)),
        'relationship_type': junk_or(pick(TYPES))})


def op_create_rel_same_tree():
    """Mostly-valid links, so the rules (not just validation) get exercised."""
    t = rng.choice(list(FamilyTree.objects.all()) or [None])
    if t is None:
        return
    pool = ids(FamilyMember, tree=t)
    if len(pool) < 2:
        return
    a, b = rng.sample(pool, 2)
    call(rng.choice([t.owner, rng.choice(users)]), 'post', '/api/relationships/',
         {'tree': t.id, 'member_1': a, 'member_2': b, 'relationship_type': rng.choice(TYPES)})


def op_patch_rel():
    pool = ids(FamilyMember)
    d = {'tree': pick(ids(FamilyTree)), 'member_1': pick(pool), 'member_2': pick(pool), 'relationship_type': pick(TYPES)}
    for k in rng.sample(list(d), rng.randint(1, 4)):
        pass
    d = {k: v for k, v in d.items() if rng.random() < 0.5}
    call(actor(), 'patch', f'/api/relationships/{pick(ids(Relationship))}/', d)


def op_delete_rel():
    call(actor(), 'delete', f'/api/relationships/{pick(ids(Relationship))}/')


def op_tree():
    u = actor(); k = rng.random()
    if k < 0.2:
        call(u, 'post', '/api/family-trees/', {'tree_name': junk_or('New tree'), 'description': junk_or('d')})
    elif k < 0.5:
        call(u, 'patch', f'/api/family-trees/{pick(ids(FamilyTree))}/', {'tree_name': junk_or('Renamed'), 'approval_required': junk_or(rng.random() < 0.5)})
    elif k < 0.6:
        if rng.random() < 0.3:  # deleting trees is rarer so there is still something to fuzz
            call(u, 'delete', f'/api/family-trees/{pick(ids(FamilyTree))}/')
    elif k < 0.8:
        call(u, 'post', f'/api/family-trees/{pick(ids(FamilyTree))}/leave/', {})
    else:
        call(u, 'get', rng.choice(['/api/family-trees/', f'/api/family-trees/{pick(ids(FamilyTree))}/']))


def op_codes():
    u = actor(); k = rng.random()
    if k < 0.35:
        call(u, 'post', '/api/family-codes/generate/', {'tree_id': junk_or(pick(ids(FamilyTree)))})
    elif k < 0.75:
        codes = list(FamilyCode.objects.values_list('code', flat=True))
        code = rng.choice(codes) if codes and rng.random() < 0.85 else junk_or('ZZZZZZ')
        call(u, 'post', '/api/family-codes/redeem/', {'code': code})
    else:
        codes = list(FamilyCode.objects.values_list('code', flat=True))
        code = rng.choice(codes) if codes and rng.random() < 0.85 else junk_or('ZZZZZZ')
        call(u, 'post', '/api/join-requests/', rng.choice([{'code': code, 'message': junk_or('hi')}, {'tree': pick(ids(FamilyTree))}]))


def op_join_decide():
    r = pick(ids(JoinRequest))
    call(actor(), rng.choice(['patch', 'get']), f'/api/join-requests/{r}/', {'status': junk_or(rng.choice(['approved', 'rejected']))})


def op_profile():
    u = actor()
    call(u, 'patch', '/api/users/me/', {k: junk_or(v) for k, v in rng.sample([
        ('email_public', rng.random() < 0.5), ('phone_public', rng.random() < 0.5), ('address_public', rng.random() < 0.5),
        ('is_superuser', True), ('is_staff', True), ('email', 'hacker@example.com'), ('first_name', 'Renamed'),
        ('phone', 'PH-U-NEW'), ('address', 'AD-U-NEW')], rng.randint(1, 4))})
    call(u, 'get', '/api/users/me/')


def op_community():
    u = actor(); k = rng.random(); cid = pick(ids(Community))
    if k < 0.12:
        call(u, 'post', '/api/communities/', {'name': junk_or(rng.choice(['Village', 'Church', 'Club'])), 'description': junk_or('d')})
    elif k < 0.22:
        call(u, 'get', f'/api/communities/find/?q={rng.choice(["Vi", "Ch", "x", "", "%", "Village"])}')
    elif k < 0.40:
        call(u, 'post', f'/api/communities/{cid}/join/', {'message': junk_or('hello'), 'tree_id': junk_or(pick(ids(FamilyTree), (None, 99999)))})
    elif k < 0.55:
        r = pick(ids(CommunityJoinRequest))
        call(u, 'patch', f'/api/community-requests/{r}/', {'status': junk_or(rng.choice(['approved', 'rejected']))})
    elif k < 0.67:
        call(u, 'post', f'/api/communities/{cid}/trees/', {'tree_id': junk_or(pick(ids(FamilyTree)))})
    elif k < 0.74:
        call(u, 'delete', f'/api/communities/{cid}/trees/{pick(ids(FamilyTree))}/')
    elif k < 0.80:
        call(u, 'post', f'/api/communities/{cid}/leave/', {})
    elif k < 0.85:
        call(u, 'delete', f'/api/communities/{cid}/members/{pick(USER_IDS)}/')
    elif k < 0.87:
        if rng.random() < 0.4:
            call(u, 'delete', f'/api/communities/{cid}/')
    elif k < 0.95:
        q = rng.choice(['', 'Ann', 'bo', 'zz', 'Ann Fz', '😀', 'x' * 80])
        params = '&'.join(f'{a}={b}' for a, b in [
            ('q', q), ('gender', rng.choice(['male', 'female', 'male,female', 'zzz', ''])),
            ('age_min', rng.choice(['', '0', '20', '-1', 'abc', '200'])), ('age_max', rng.choice(['', '30', '120', '5'])),
            ('living', rng.choice(['', 'yes', 'no'])), ('limit', rng.choice(['', '5', '0', '9999', 'x'])), ('offset', rng.choice(['', '3', '-5']))] if rng.random() < 0.6)
        call(u, 'get', f'/api/communities/{cid}/people/?{params}')
    else:
        call(u, 'get', rng.choice([f'/api/communities/{cid}/', f'/api/communities/{cid}/requests/', f'/api/communities/{cid}/members/', '/api/communities/']))


def op_staff():
    u = actor(); tid = pick(ids(FamilyTree)); k = rng.random()
    if k < 0.3:
        call(u, 'get', rng.choice(['/api/staff/trees/', f'/api/staff/trees/{tid}/']))
    elif k < 0.6:
        call(u, 'post', f'/api/staff/trees/{tid}/members/', rand_member_payload(tid))
    elif k < 0.8:
        call(u, 'patch', f'/api/staff/trees/{tid}/members/{pick(ids(FamilyMember))}/', rand_member_payload(tid, full=False))
    else:
        pool = ids(FamilyMember)
        call(u, 'post', f'/api/staff/trees/{tid}/relationships/', {'tree': tid, 'member_1': pick(pool), 'member_2': pick(pool), 'relationship_type': pick(TYPES)})


def op_reads():
    u = actor(); tid = pick(ids(FamilyTree))
    call(u, 'get', rng.choice([
        f'/api/family-members/?tree_id={tid}', f'/api/relationships/?tree_id={tid}', f'/api/edit-history/?tree_id={tid}',
        f'/api/family-members/{pick(ids(FamilyMember))}/', '/api/relationship-types/', '/api/join-requests/mine/',
        f'/api/join-requests/?tree_id={tid}', '/api/family-members/', '/api/relationships/', '/api/edit-history/']))


OPS = [(op_create_member, 8), (op_patch_member, 9), (op_delete_member, 3), (op_create_rel, 4), (op_create_rel_same_tree, 14),
       (op_patch_rel, 7), (op_delete_rel, 3), (op_tree, 6), (op_codes, 8), (op_join_decide, 4), (op_profile, 5),
       (op_community, 16), (op_staff, 3), (op_reads, 6)]
OP_FUNCS = [f for f, w in OPS for _ in range(w)]

# ---------------------------------------------------------------- invariants
def check_invariants(when):
    # relationships stay inside one family, one link per pair, no parent loops
    seen, children = {}, {}
    for r in Relationship.objects.select_related('relationship_type', 'member_1', 'member_2'):
        if not (r.member_1.tree_id == r.member_2.tree_id == r.tree_id):
            fail(f'[{when}] relationship {r.id} joins people from different families')
        key = (r.tree_id, *sorted((r.member_1_id, r.member_2_id)))
        if key in seen:
            fail(f'[{when}] people {key[1]} and {key[2]} have two relationships ({seen[key]} and {r.id})')
        seen[key] = r.id
        e = ancestor_edge(r.relationship_type.type_name, r.member_1_id, r.member_2_id)
        if e:
            children.setdefault(e[0], set()).add(e[1])
    state = {}

    def visit(n):
        state[n] = 1
        for c in children.get(n, ()):
            if state.get(c) == 1:
                return True
            if c not in state and visit(c):
                return True
        state[n] = 2
        return False
    if any(n not in state and visit(n) for n in list(children)):
        fail(f'[{when}] parent links form a loop')
    # consistency
    for t in FamilyTree.objects.filter(is_active=True):
        if not TreeMember.objects.filter(tree=t, user=t.owner).exists():
            fail(f'[{when}] family {t.id} lost its owner membership')
    for c in Community.objects.all():
        if not CommunityMember.objects.filter(community=c, user=c.owner, role='owner').exists():
            fail(f'[{when}] community {c.id} lost its owner membership')
    for ct in CommunityTree.objects.select_related('tree'):
        if not CommunityMember.objects.filter(community_id=ct.community_id, user=ct.tree.owner).exists():
            fail(f'[{when}] family {ct.tree_id} is shared in community {ct.community_id} but its owner is not a member')
    for m in FamilyMember.objects.exclude(user=None):
        if not TreeMember.objects.filter(tree_id=m.tree_id, user_id=m.user_id).exists():
            fail(f'[{when}] person {m.id} is linked to account {m.user_id} that is not in the family')
    if User.objects.filter(is_superuser=True).exclude(id=users[5].id).exists():
        fail(f'[{when}] someone other than the seeded admin became superuser')


def scan(when):
    """Every response, for every viewer, must not carry a private value the viewer may not see."""
    members = list(FamilyMember.objects.select_related('tree'))
    by_user = {u.id: u for u in User.objects.all()}
    for viewer in users + [None]:
        vid = viewer.id if viewer else None
        urls = ['/api/family-trees/', '/api/users/me/', '/api/communities/']
        for t in FamilyTree.objects.all():
            urls += [f'/api/family-trees/{t.id}/', f'/api/family-members/?tree_id={t.id}', f'/api/relationships/?tree_id={t.id}',
                     f'/api/edit-history/?tree_id={t.id}']
            is_member = viewer is not None and TreeMember.objects.filter(tree=t, user=viewer).exists()
            if not is_member or not t.is_active:
                for path in urls[-3:]:
                    r = call(viewer, 'get', path)
                    if r is not None and r.status_code == 200:
                        fail(f'[{when}] {("u" + str(vid)) if viewer else "anon"} was allowed to read {path} (member={is_member}, active={t.is_active})')
        for c in Community.objects.all():
            urls.append(f'/api/communities/{c.id}/people/?limit=50')
        for path in urls:
            r = call(viewer, 'get', path)
            if r is None:
                continue
            text = r.content.decode('utf-8', 'replace')
            for m in members:
                owner_or_self = viewer is not None and (m.tree.owner_id == vid or m.user_id == vid)
                community = '/people/' in path
                for sentinel, flag in ((f'PH-M{m.id}~', m.phone_public), (f'm{m.id}-priv@example.com', m.email_public),
                                       (f'AD-M{m.id}-SECRET', m.address_public)):
                    if sentinel in text:
                        allowed = (flag if community else (flag or owner_or_self))
                        if community and 'm' in sentinel[:1] or (community and sentinel.startswith('AD-')):
                            allowed = False  # communities never show email or address
                        if not allowed or (not m.tree.is_active and community):
                            fail(f'[{when}] {sentinel} appeared in {path} for {"u" + str(vid) if viewer else "anon"} (public={flag})')
            for u in users:
                if u.id == vid:
                    continue
                db = by_user[u.id]
                for sentinel, flag in ((f'PH-U{u.id - users[0].id}-SECRET', db.phone_public), (f'AD-U{u.id - users[0].id}-SECRET', db.address_public)):
                    if sentinel in text and not flag:
                        fail(f'[{when}] account detail {sentinel} appeared in {path} for {"u" + str(vid) if viewer else "anon"}')
                if f'fz{u.id - users[0].id}@example.com' in text and not db.email_public and path.startswith(('/api/family-trees', '/api/edit-history', '/api/family-members')):
                    addr = f'fz{u.id - users[0].id}@example.com'
                    at = text.index(addr)
                    fail(f'[{when}] email of u{u.id} appeared in {path} for {"u" + str(vid) if viewer else "anon"} while hidden: ...{text[max(0, at - 90):at + 40]}...')


# ---------------------------------------------------------------- run
for i in range(ROUNDS):
    try:
        rng.choice(OP_FUNCS)()
    except Exception:  # noqa: BLE001
        fail(f'fuzzer itself broke at op {i}: {traceback.format_exc(limit=3)}')
    if i % 100 == 99:
        check_invariants(f'after {i + 1} operations')
    if i % 200 == 199:
        scan(f'after {i + 1} operations')
    if len(failures) >= 12:
        break
check_invariants('end')
scan('end')

stats = f'{ROUNDS} random requests, {FamilyMember.objects.count()} people, {Relationship.objects.count()} links, ' \
        f'{FamilyTree.objects.count()} families, {Community.objects.count()} communities'
if failures:
    seen = set()
    for f in failures:
        head = f.splitlines()[0][:140]
        if head not in seen:
            seen.add(head)
            print('FAIL ' + f)
    print(f'\nSeed {SEED}. Last requests before the first problem:')
    print('\n'.join('   ' + l for l in op_log))
    raise SystemExit(1)
print(f'PASS no server errors in {ROUNDS} random requests (seed {SEED})')
print('PASS links never cross families, never double up, never loop')
print('PASS private details never leaked to anyone not entitled')
print('PASS strangers and deleted families stay locked out')
print('PASS owners, members and shared families stay consistent')
print('   ' + stats)
