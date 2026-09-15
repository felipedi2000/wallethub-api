from django.urls import path
from .views import (
    UserRegisterView,
    UserProfileView,
    LogoutView,
    ChangePasswordView,
    DeviceListCreateView,
    DeviceRetrieveUpdateDestroyView,
    UserSearchView,
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
)

urlpatterns = [
    path("login/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("refresh/", CustomTokenRefreshView.as_view(), name="token_refresh"),
    path("logout/", LogoutView.as_view(), name="user_logout"),
    
    path("register/", UserRegisterView.as_view(), name="user_register"),
    
    path("me/", UserProfileView.as_view(), name="user_profile"),
    path("change-password/", ChangePasswordView.as_view(), name="change_password"),
    
    path("devices/", DeviceListCreateView.as_view(), name="device_list_create"),
    path("devices/<uuid:pk>/", DeviceRetrieveUpdateDestroyView.as_view(), name="device_detail"),
    
    path("search/", UserSearchView.as_view(), name="user-search"),
]