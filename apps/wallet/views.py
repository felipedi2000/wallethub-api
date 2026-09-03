from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, generics
from .models import TransactionLimit
from .serializers import TransactionLimitSerializer, WalletSerializer

class TransactionLimitViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Permite al usuario autenticado consultar el estado de sus limites y consumos.
    """
    serializer_class = TransactionLimitSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # seguridad   eguridad: filtra directamente por el usuario del token JWT
        return TransactionLimit.objects.filter(user=self.request.user)

class UserWalletView(generics.RetrieveAPIView):
    """
    GET /api/v1/wallet/me/
    """
    serializer_class = WalletSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # Obtiene directamente la billetera vinculada al usuario autenticado
        return self.request.user.wallet