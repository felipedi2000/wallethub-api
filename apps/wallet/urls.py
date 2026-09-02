from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TransactionLimitViewSet, UserWalletView

app_name = "wallet"

router = DefaultRouter()
# incluir rutas por deecto de viewset
router.register(r"limits", TransactionLimitViewSet, basename="transaction_limit")

urlpatterns = [
  path("", include(router.urls)),
  path("me/", UserWalletView.as_view(), name="user_wallet"),
]