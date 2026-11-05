def normalized_username(request, credentials):
    """
    The name django-axes counts failed logins against.

    MySQL matches emails case-insensitively, so `Boss@x.com` and ` boss@x.com ` are the SAME
    account at login. Counting them separately would give an attacker a fresh set of guesses
    for every spelling; normalising makes them share one lockout.
    """
    username = (credentials or {}).get('username')
    if username is None and request is not None:
        username = getattr(request, 'POST', {}).get('username')
    return (username or '').strip().lower()
