from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserWalletView

app_name = "wallet"


urlpatterns = [
  path("me/", UserWalletView.as_view(), name="user_wallet"),
]