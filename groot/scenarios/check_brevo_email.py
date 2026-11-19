"""The Brevo email backend, with the network replaced by a stand-in: nothing is ever really sent."""
import io
import json
import os
import urllib.error
from unittest import mock

import django

django.setup()
from django.conf import settings  # noqa: E402
from django.core.mail import EmailMessage, get_connection  # noqa: E402

fails = []


def chk(cond, msg):
    print(('PASS ' if cond else 'FAIL ') + msg)
    if not cond:
        fails.append(msg)


settings.BREVO_API_KEY = 'test-key'
BACKEND = 'utils.brevo_backend.BrevoEmailBackend'


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


sent = []


def fake_ok(request, timeout=None):
    sent.append((request, timeout))
    return FakeResponse(b'{"messageId":"<x@y>"}')


msg = EmailMessage('Bob wants to join Village', 'Review it here: https://kinship.test/approve/community/3',
                   'Kinship <kinshiptrees@gmail.com>', ['owner@example.com'])
with mock.patch('urllib.request.urlopen', fake_ok):
    n = get_connection(BACKEND).send_messages([msg])
req, timeout = sent[0]
body = json.loads(req.data)
chk(n == 1, 'one message sent')
chk(req.full_url == 'https://api.brevo.com/v3/smtp/email' and req.get_method() == 'POST', 'goes to Brevo\'s web API over HTTPS')
chk(req.get_header('Api-key') == 'test-key', 'sends the API key in the header, not in the body')
chk('test-key' not in req.data.decode(), 'the key is never put in the message body')
chk(body['sender'] == {'email': 'kinshiptrees@gmail.com', 'name': 'Kinship'}, f'sender is the verified address: {body["sender"]}')
chk(body['to'] == [{'email': 'owner@example.com'}] and body['subject'] == msg.subject and 'approve/community/3' in body['textContent'], 'recipient, subject and link are all there')
chk(timeout and timeout <= 30, 'has a timeout so a slow reply cannot hang the server')

# a refusal (e.g. sender not verified) must be reported, not swallowed
def fake_refuse(request, timeout=None):
    raise urllib.error.HTTPError(request.full_url, 400, 'Bad Request', {}, io.BytesIO(b'{"message":"Sender is not valid"}'))


with mock.patch('urllib.request.urlopen', fake_refuse):
    try:
        get_connection(BACKEND).send_messages([msg])
        chk(False, 'a refused email should raise')
    except RuntimeError as e:
        chk('Sender is not valid' in str(e), 'a refusal is raised with Brevo\'s explanation')
    chk(get_connection(BACKEND, fail_silently=True).send_messages([msg]) == 0, 'fail_silently returns 0 instead of raising')

# no internet at all
with mock.patch('urllib.request.urlopen', side_effect=urllib.error.URLError('no route')):
    try:
        get_connection(BACKEND).send_messages([msg])
        chk(False, 'a network failure should raise')
    except urllib.error.URLError:
        chk(True, 'a network failure is raised (utils/notify.py logs it and the join request still works)')

# the right backend is chosen from the settings
import importlib  # noqa: E402

for env, expected in [({'BREVO_API_KEY': 'k'}, 'utils.brevo_backend.BrevoEmailBackend'),
                      ({'EMAIL_HOST_PASSWORD': 'p'}, 'utils.mail_backend.IPv4EmailBackend'),
                      ({'BREVO_API_KEY': 'k', 'EMAIL_HOST_PASSWORD': 'p'}, 'utils.brevo_backend.BrevoEmailBackend'),
                      ({}, 'django.core.mail.backends.dummy.EmailBackend')]:
    with mock.patch.dict(os.environ, {'DEBUG': 'False', 'BREVO_API_KEY': '', 'EMAIL_HOST_PASSWORD': '', **env}):
        import config.settings as cs
        importlib.reload(cs)
        chk(cs.EMAIL_BACKEND == expected, f'settings with {sorted(env) or "nothing set"} -> {cs.EMAIL_BACKEND.split(".")[-2]}')

print('FAILURES:', fails or 'none')
raise SystemExit(1 if fails else 0)
