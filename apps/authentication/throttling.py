# throttling.py
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

class UserSearchRateThrottle(UserRateThrottle):
    scope = 'user_search'

class StrictAnonRateThrottle(AnonRateThrottle):
    scope = 'auth_strict'