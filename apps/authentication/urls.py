from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import DeviceListCreateView, DeviceRetrieveUpdateDestroyView, UserProfileView, UserRegisterView, LogoutView, ChangePasswordView, UserSearchView

app_name = "authentication"

urlpatterns = [
    path("register/", UserRegisterView.as_view(), name="user_register"),
    path("login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("me/", UserProfileView.as_view(), name="user_profile"),
    path("logout/", LogoutView.as_view(), name="user_logout"),
    path(
        "change-password/",
        ChangePasswordView.as_view(),
        name="change_password",
    ),
    path("devices/", DeviceListCreateView.as_view(), name="device_list_create"),
    path("devices/<uuid:pk>/", DeviceRetrieveUpdateDestroyView.as_view(), name="device_detail"),
    path("search/", UserSearchView.as_view(), name="user-search"),
]