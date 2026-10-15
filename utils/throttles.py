from rest_framework.throttling import UserRateThrottle


class CodeAttemptThrottle(UserRateThrottle):
    """Limits how many family-code guesses one account can make (see DEFAULT_THROTTLE_RATES)."""
    scope = 'code_attempts'
