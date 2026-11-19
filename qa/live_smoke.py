"""
Read-only checks against the LIVE website. Nothing here signs in, creates or changes anything: it
only asks for pages and expects the server to turn anonymous requests away properly.

    python qa/live_smoke.py
"""
import json
import re
import sys
import urllib.error
import urllib.request

SITES = {
    'netlify': 'https://kinship-family.netlify.app',
    'railway': 'https://family-tree-backend-production.up.railway.app',
}
fails = []


def check(cond, msg):
    print(('PASS ' if cond else 'FAIL ') + msg)
    if not cond:
        fails.append(msg)


def fetch(url, method='GET', body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={'User-Agent': 'KinshipQA/1.0', 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:  # noqa: BLE001
        return 0, str(e).encode()


bundles = {}
for name, base in SITES.items():
    code, html = fetch(base + '/')
    text = html.decode('utf-8', 'replace')
    check(code == 200 and '<div id="root"' in text, f'{name}: home page loads')
    js = re.search(r'/assets/(index-[\w-]+\.js)', text)
    css = re.search(r'/assets/(index-[\w-]+\.css)', text)
    bundles[name] = js.group(1) if js else None
    check(bool(js and css), f'{name}: page points at its script and stylesheet')
    if js:
        c, body = fetch(f'{base}/assets/{js.group(1)}')
        check(c == 200 and len(body) > 100_000, f'{name}: script downloads ({len(body) // 1024} KB)')
    if css:
        c, body = fetch(f'{base}/assets/{css.group(1)}')
        check(c == 200 and len(body) > 5_000, f'{name}: stylesheet downloads')
    for page in ('/communities', '/approve/community/1', '/login', '/profile'):
        c, body = fetch(base + page)
        check(c == 200 and b'<div id="root"' in body, f'{name}: deep link {page} opens the app')
check(bundles['netlify'] == bundles['railway'], 'both addresses serve the same version')

PROTECTED = [
    ('GET', '/api/users/me/'), ('GET', '/api/users/me/avatar/'), ('GET', '/api/family-trees/'),
    ('GET', '/api/family-members/?tree_id=1'), ('GET', '/api/relationships/?tree_id=1'), ('GET', '/api/edit-history/?tree_id=1'),
    ('GET', '/api/communities/'), ('GET', '/api/communities/1/people/'), ('GET', '/api/join-requests/mine/'),
    ('GET', '/api/staff/trees/'), ('POST', '/api/family-codes/redeem/'), ('POST', '/api/communities/'),
    ('PATCH', '/api/users/me/'), ('DELETE', '/api/family-members/1/'), ('DELETE', '/api/relationships/1/'),
]
for name, base in SITES.items():
    for method, path in PROTECTED:
        code, _ = fetch(base + path, method, {} if method in ('POST', 'PATCH') else None)
        check(code == 401, f'{name}: {method} {path} turns anonymous visitors away (got {code})')
    code, body = fetch(base + '/api/auth/google/', 'POST', {})
    check(code == 400 and b'id_token' in body, f'{name}: sign-in without a token is a clear 400')
    code, _ = fetch(base + '/api/auth/google/', 'POST', {'id_token': 'garbage'})
    check(code in (400, 401), f'{name}: sign-in with a fake token is refused, not a crash (got {code})')
    code, _ = fetch(base + '/api/nope/')
    check(code in (401, 404), f'{name}: unknown API path is not a server error (got {code})')

print()
print('FAILURES:', fails or 'none')
sys.exit(1 if fails else 0)
