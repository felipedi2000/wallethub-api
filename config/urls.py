# config/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from drf_spectacular.views import (
    SpectacularSwaggerView,
    SpectacularRedocView,
    SpectacularAPIView,
)
from apps.shared.views import custom_404_handler, custom_500_handler

urlpatterns = [
    path("api/v1/auth/", include("apps.authentication.urls")),
    path("api/v1/wallet/", include(("apps.wallet.urls", "wallet"), namespace="wallet")),
    path("api/v1/transactions/", include(("apps.transactions.urls", "transactions"), namespace="transactions")),
    
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

if settings.ENABLE_ADMIN:
    urlpatterns.append(path("admin/", admin.site.urls))

handler404 = custom_404_handler
handler500 = custom_500_handler