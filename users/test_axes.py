"""Admin login lockout (django-axes): brute-forcing /admin/ is stopped, nothing else is affected."""
from datetime import timedelta
from unittest import mock

from axes.models import AccessAttempt
from django.test import Client, TestCase, override_settings
from django.utils import timezone

from config.testing import client_for, make_user
from users.models import User

PASSWORD = 'correct-horse-battery-staple'
AXES_BACKENDS = ['axes.backends.AxesStandaloneBackend', 'django.contrib.auth.backends.ModelBackend']


def attempt(client, email, password):
    return client.post('/admin/login/', {'username': email, 'password': password, 'next': '/admin/'})


@override_settings(AUTHENTICATION_BACKENDS=AXES_BACKENDS)
class AdminLockoutTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(email='boss@example.com', google_id='gb', password=PASSWORD)
        self.other = User.objects.create_superuser(email='other@example.com', google_id='go', password=PASSWORD)

    def bad_logins(self, times, email='boss@example.com', client=None):
        client = client or Client()
        return [attempt(client, email, 'wrong-password').status_code for _ in range(times)]

    def test_production_settings_wire_axes_in(self):
        import config.settings as prod
        self.assertEqual(prod.AUTHENTICATION_BACKENDS, AXES_BACKENDS)
        self.assertIn('axes', prod.INSTALLED_APPS)
        self.assertIn('axes.middleware.AxesMiddleware', prod.MIDDLEWARE)
        self.assertTrue(prod.AXES_ONLY_ADMIN_SITE)
        self.assertEqual(prod.AXES_FAILURE_LIMIT, 5)

    def test_correct_password_still_logs_in_normally(self):
        client = Client()
        res = attempt(client, 'boss@example.com', PASSWORD)
        self.assertEqual(res.status_code, 302)
        self.assertEqual(client.get('/admin/').status_code, 200)

    def test_five_wrong_passwords_lock_the_account_out_even_for_the_right_one(self):
        client = Client()
        # Attempts 1-4 are refused with the form shown again; the 5th trips the lock.
        self.assertEqual(self.bad_logins(5, client=client), [200] * 4 + [429])
        res = attempt(client, 'boss@example.com', PASSWORD)  # the CORRECT password now
        self.assertEqual(res.status_code, 429)
        self.assertEqual(client.get('/admin/').status_code, 302)  # not signed in

    def test_changing_browser_or_session_does_not_get_around_the_lock(self):
        self.bad_logins(5)
        res = attempt(Client(), 'boss@example.com', PASSWORD)  # brand-new client
        self.assertEqual(res.status_code, 429)

    def test_spoofed_client_addresses_do_not_get_around_the_lock(self):
        for i in range(5):
            Client().post('/admin/login/', {'username': 'boss@example.com', 'password': 'bad'},
                          HTTP_X_FORWARDED_FOR=f'203.0.113.{i}')
        res = Client().post('/admin/login/', {'username': 'boss@example.com', 'password': PASSWORD},
                            HTTP_X_FORWARDED_FOR='198.51.100.77')
        self.assertEqual(res.status_code, 429)

    def test_case_and_whitespace_variants_of_the_email_share_one_lock(self):
        for variant in ['Boss@Example.com', ' boss@example.com ', 'BOSS@EXAMPLE.COM', 'boss@example.com', 'bOsS@example.com']:
            attempt(Client(), variant, 'bad')
        res = attempt(Client(), 'boss@example.com', PASSWORD)
        self.assertEqual(res.status_code, 429)

    def test_locking_one_account_leaves_other_accounts_alone(self):
        self.bad_logins(5)
        res = attempt(Client(), 'other@example.com', PASSWORD)
        self.assertEqual(res.status_code, 302)

    def test_four_failures_then_success_clears_the_count(self):
        self.bad_logins(4)
        client = Client()
        self.assertEqual(attempt(client, 'boss@example.com', PASSWORD).status_code, 302)
        client.logout()
        self.assertEqual(self.bad_logins(4), [200] * 4)  # fresh budget: still not locked
        self.assertEqual(attempt(Client(), 'boss@example.com', PASSWORD).status_code, 302)

    def test_the_lock_expires_after_the_cooloff(self):
        self.bad_logins(5)
        self.assertEqual(attempt(Client(), 'boss@example.com', PASSWORD).status_code, 429)
        AccessAttempt.objects.update(attempt_time=timezone.now() - timedelta(minutes=31))
        self.assertEqual(attempt(Client(), 'boss@example.com', PASSWORD).status_code, 302)

    def test_guessing_made_up_accounts_is_limited_too(self):
        self.bad_logins(5, email='nobody@example.com')
        self.assertEqual(attempt(Client(), 'nobody@example.com', 'x').status_code, 429)

    def test_the_admin_can_unlock_with_axes_reset(self):
        from django.core.management import call_command
        self.bad_logins(5)
        call_command('axes_reset')
        self.assertEqual(attempt(Client(), 'boss@example.com', PASSWORD).status_code, 302)


@override_settings(AUTHENTICATION_BACKENDS=AXES_BACKENDS)
class LockoutStaysInTheAdminTests(TestCase):
    """Only /admin/ login is rate-limited: the app's own sign-in and API must never be locked out."""

    def setUp(self):
        self.admin = User.objects.create_superuser(email='boss@example.com', google_id='gb', password=PASSWORD)

    def lock_admin_login(self):
        for _ in range(5):
            attempt(Client(), 'boss@example.com', 'wrong-password')
        self.assertEqual(attempt(Client(), 'boss@example.com', PASSWORD).status_code, 429)

    def test_a_locked_admin_login_does_not_block_that_users_api_access(self):
        self.lock_admin_login()
        res = client_for(self.admin).get('/api/users/me/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['email'], 'boss@example.com')

    def test_repeated_failed_google_sign_ins_are_never_locked_out(self):
        with mock.patch('users.views.verify_google_token', side_effect=ValueError('Invalid Google token')):
            codes = {Client().post('/api/auth/google/', {'id_token': 'bad'}, content_type='application/json').status_code
                     for _ in range(12)}
        self.assertEqual(codes, {401})

    def test_failed_attempts_outside_the_admin_are_not_recorded(self):
        Client().post('/api/auth/google/', {'id_token': 'bad'}, content_type='application/json')
        self.assertEqual(AccessAttempt.objects.count(), 0)

    def test_ordinary_users_can_still_use_the_api_during_an_admin_lockout(self):
        plain = make_user('plain')
        self.lock_admin_login()
        self.assertEqual(client_for(plain).get('/api/family-trees/').status_code, 200)
