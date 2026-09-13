from rest_framework.throttling import UserRateThrottle
from rest_framework.exceptions import Throttled
from rest_framework.throttling import AnonRateThrottle

class CustomUserRateThrottle(UserRateThrottle):
    scope = "user"

    def throttle_failure(self):
        raise Throttled(
            detail="Has realizado demasiadas solicitudes. Por favor, espera antes de intentar nuevamente.",
            wait=self.wait(),
        )


class TransactionThrottle(UserRateThrottle):
    """Throttle para transacciones"""
    scope = "transactions"

    def throttle_failure(self):
        raise Throttled(
            detail="Has superado el límite de transacciones permitidas. Por favor, espera antes de intentar nuevamente.",
            wait=self.wait(),
        )

class CustomAnonRateThrottle(AnonRateThrottle):
    scope = "anon"

    def throttle_failure(self):
        raise Throttled(
            detail="Has realizado demasiadas solicitudes. Por favor, regístrate o espera antes de intentar nuevamente.",
            wait=self.wait(),
        )

class UserSearchRateThrottle(UserRateThrottle):
    scope = "user_search"

    def throttle_failure(self):
        raise Throttled(
            detail="Has realizado demasiadas búsquedas de usuarios. Por favor, espera antes de intentar nuevamente.",
            wait=self.wait(),
        )


class StrictAnonRateThrottle(UserRateThrottle):
    scope = "auth_strict"

    def throttle_failure(self):
        raise Throttled(
            detail="Has excedido el límite de intentos. Por favor, espera antes de intentar nuevamente.",
            wait=self.wait(),
        )