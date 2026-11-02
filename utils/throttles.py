from rest_framework.throttling import UserRateThrottle


class CodeAttemptThrottle(UserRateThrottle):
    """Limits how many family-code guesses one account can make (see DEFAULT_THROTTLE_RATES)."""
    scope = 'code_attempts'


class CommunitySearchThrottle(UserRateThrottle):
    """Caps people-search requests per account so the directory cannot be scraped."""
    scope = 'community_search'


class CommunityFindThrottle(UserRateThrottle):
    """Caps community-name lookups per account so the list of communities cannot be enumerated."""
    scope = 'community_find'
