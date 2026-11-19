"""
Email through Brevo's web API instead of SMTP. Railway blocks the usual outgoing mail ports on our plan,
but ordinary HTTPS (port 443) is open, so mail goes out as one web request per message.
"""
import json
import logging
import urllib.error
import urllib.request
from email.utils import parseaddr

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

log = logging.getLogger(__name__)
API_URL = 'https://api.brevo.com/v3/smtp/email'


class BrevoEmailBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        sent = 0
        for message in email_messages:
            try:
                self._send(message)
                sent += 1
            except Exception:  # noqa: BLE001 - let notify.py log it; fail_silently is honoured below
                if not self.fail_silently:
                    raise
                log.exception('Brevo could not send "%s"', message.subject)
        return sent

    def _send(self, message):
        name, address = parseaddr(message.from_email or settings.DEFAULT_FROM_EMAIL)
        payload = {
            'sender': {'email': address, **({'name': name} if name else {})},
            'to': [{'email': to} for to in message.to],
            'subject': message.subject,
            'textContent': message.body,
        }
        request = urllib.request.Request(
            API_URL,
            data=json.dumps(payload).encode('utf-8'),
            method='POST',
            headers={
                'api-key': settings.BREVO_API_KEY,
                'accept': 'application/json',
                'content-type': 'application/json',
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=settings.EMAIL_TIMEOUT) as response:
                response.read()
        except urllib.error.HTTPError as e:
            # Brevo explains itself in the body (e.g. "sender not verified"); keep that for the logs.
            raise RuntimeError(f'Brevo refused the email ({e.code}): {e.read().decode("utf-8", "replace")[:300]}') from e
