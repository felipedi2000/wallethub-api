from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, generics
from .serializers import WalletSerializer

class UserWalletView(generics.RetrieveAPIView):
    """
    GET /api/v1/wallet/me/
    """
    serializer_class = WalletSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # Obtiene directamente la billetera vinculada al usuario autenticado
        return self.request.user.wallet