from django.contrib import admin
from django.urls import path, include
from config import settings


urlpatterns = [
  path("api/v1/auth/", include("apps.authentication.urls")),
  path("api/v1/wallet/", include(("apps.wallet.urls", "wallet"), namespace="wallet")),
  path("api/v1/transacions", include(("apps.transactions.urls", "transactions"), namespace="transactions"))
]

if settings.ENABLE_ADMIN:
  urlpatterns.append(path("admin/", admin.site.urls))