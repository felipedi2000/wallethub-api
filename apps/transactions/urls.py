from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.transactions.views import TransactionViewSet, UserLimitsMeAPIView

router = DefaultRouter()
router.register(r"", TransactionViewSet, basename="transaction")

urlpatterns = [
    path("limits/me/", UserLimitsMeAPIView.as_view(), name="user-limits-me"),
]

urlpatterns += router.urls