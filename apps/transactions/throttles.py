from rest_framework.throttling import UserRateThrottle

class TransactionThrottle(UserRateThrottle):
  scope= "transaction"