from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, generics
from .serializers import WalletSerializer
from apps.shared.throttles import CustomUserRateThrottle

class UserWalletView(generics.RetrieveAPIView):
    serializer_class = WalletSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [CustomUserRateThrottle]

    def get_object(self):
        return self.request.user.wallet