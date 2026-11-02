"""Emails to owners about join requests. Sending never blocks or breaks the request that caused it."""
import logging
import threading

from django.conf import settings
from django.core.mail import send_mail

log = logging.getLogger(__name__)


def site_link(path, request=None):
    """Absolute link to a page of the website (SITE_URL, else the first allowed web origin)."""
    base = settings.SITE_URL
    if not base and request is not None:
        base = request.build_absolute_uri('/').rstrip('/')
    return f'{base}{path}'


def email_owner(owner, subject, body):
    """Fire-and-forget plain-text email. Does nothing (and logs why) if email is not set up."""
    if not owner.email:
        return
    if settings.EMAIL_BACKEND.endswith('dummy.EmailBackend'):
        log.info('Email not configured; skipped "%s" to user %s', subject, owner.id)
        return
    subject = ' '.join(subject.split())[:150]  # no line breaks in a header

    def run():
        try:
            send_mail(subject, body, None, [owner.email], fail_silently=False)
        except Exception:  # noqa: BLE001 - a mail outage must never surface to users
            log.exception('Could not email join request notice to user %s', owner.id)

    threading.Thread(target=run, daemon=True).start()
