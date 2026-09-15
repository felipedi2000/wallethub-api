from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, generics
from .serializers import WalletSerializer
from apps.shared.throttles import CustomUserRateThrottle
from drf_spectacular.utils import extend_schema

@extend_schema(
    tags=["Wallet"],
    summary="Obtener billetera del usuario",
    description="Devuelve la información de la billetera asociada al usuario autenticado, incluyendo su saldo actual, moneda y ID de cuenta.",
)
class UserWalletView(generics.RetrieveAPIView):
    """Obtener billetera del usuario autenticado"""
    serializer_class = WalletSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [CustomUserRateThrottle]

    def get_object(self):
        return self.request.user.wallet