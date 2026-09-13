# apps/users/tests/test_users_throttling.py
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APITestCase
from apps.wallet.models import Wallet
from apps.shared.throttles import (
    CustomAnonRateThrottle,
    CustomUserRateThrottle,
    UserSearchRateThrottle,
    StrictAnonRateThrottle,
)

User = get_user_model()


class UserThrottlingTestCase(APITestCase):

    def setUp(self):
        cache.clear()

        CustomAnonRateThrottle.rate = "2/minute"
        CustomUserRateThrottle.rate = "3/minute"
        UserSearchRateThrottle.rate = "2/minute"
        StrictAnonRateThrottle.rate = "2/minute"

        self.user1 = User.objects.create_user(
            first_name="usuario1",
            last_name="apellido1",
            email="user1@test.com",
            password="Password123!",
        )
        self.user2 = User.objects.create_user(
            first_name="usuario2",
            last_name="apellido2",
            email="user2@test.com",
            password="Password123!",
        )

        self.wallet1 = Wallet.objects.get(user=self.user1)
        self.wallet1.balance = Decimal("1000.00")
        self.wallet1.save()

        self.wallet2 = Wallet.objects.get(user=self.user2)
        self.wallet2.balance = Decimal("500.00")
        self.wallet2.save()

        self.client.force_authenticate(user=self.user1)

        self.profile_url = "/api/v1/auth/me/"
        self.register_url = "/api/v1/auth/register/"
        self.logout_url = "/api/v1/auth/logout/"
        self.search_url = "/api/v1/auth/search/"
        self.change_password_url = "/api/v1/auth/change-password/"
        self.devices_list_url = "/api/v1/auth/devices/"

    def tearDown(self):
        cache.clear()

    def test_user_profile_applies_user_rate_throttle(self):
        for i in range(3):
            response = self.client.get(self.profile_url, format="json")
            self.assertEqual(
                response.status_code,
                status.HTTP_200_OK,
                msg=f"La petición GET {i+1} a profile debería ser permitida."
            )

        response_throttled = self.client.get(self.profile_url, format="json")
        
        self.assertEqual(
            response_throttled.status_code,
            status.HTTP_429_TOO_MANY_REQUESTS,
            msg="La 4ª solicitud GET a profile debería ser bloqueada."
        )
        self.assertIn("detail", response_throttled.data)

    def test_user_register_applies_anon_rate_throttle(self):
        self.client.force_authenticate(user=None) 
        
        payload = {
            "email": "newuser@test.com",
            "password": "Password123!",
            "password_confirm": "Password123!",
            "first_name": "nuevo",
            "last_name": "usuario",
        }

        for i in range(2):
            email = f"newuser{i}@test.com"
            payload["email"] = email
            
            response = self.client.post(
                self.register_url,
                data=payload,
                format="json"
            )
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                msg=f"La petición POST {i+1} a register debería ser permitida."
            )

        payload["email"] = "newuser3@test.com"
        response_throttled = self.client.post(
            self.register_url,
            data=payload,
            format="json"
        )
        
        self.assertEqual(
            response_throttled.status_code,
            status.HTTP_429_TOO_MANY_REQUESTS,
            msg="La 3ª solicitud POST a register debería ser bloqueada."
        )

    def test_logout_applies_strict_rate_throttle(self):
        payload = {"refresh": "dummy_token"}

        for i in range(2):
            response = self.client.post(
                self.logout_url,
                data=payload,
                format="json"
            )

            self.assertNotEqual(
                response.status_code,
                status.HTTP_429_TOO_MANY_REQUESTS,
                msg=f"La petición POST {i+1} a logout debería ser permitida."
            )

        response_throttled = self.client.post(
            self.logout_url,
            data=payload,
            format="json"
        )
        
        self.assertEqual(
            response_throttled.status_code,
            status.HTTP_429_TOO_MANY_REQUESTS,
            msg="La 3ª solicitud POST a logout debería ser bloqueada."
        )

    def test_user_search_applies_user_search_rate_throttle(self):
        for i in range(2):
            response = self.client.get(
                self.search_url,
                {"email": self.user2.email},
                format="json"
            )
            self.assertEqual(
                response.status_code,
                status.HTTP_200_OK,
                msg=f"La petición GET {i+1} a search debería ser permitida."
            )

        response_throttled = self.client.get(
            self.search_url,
            {"email": self.user2.email},
            format="json"
        )
        
        self.assertEqual(
            response_throttled.status_code,
            status.HTTP_429_TOO_MANY_REQUESTS,
            msg="La 3ª solicitud GET a search debería ser bloqueada."
        )

    def test_change_password_applies_user_rate_throttle(self):
        payload = {
            "old_password": "Password123!",
            "new_password": "NewPassword123!",
            "new_password_confirm": "NewPassword123!",
        }

        for i in range(3):
            response = self.client.post(
                self.change_password_url,
                data=payload,
                format="json"
            )

            self.assertNotEqual(
                response.status_code,
                status.HTTP_429_TOO_MANY_REQUESTS,
                msg=f"La petición POST {i+1} a change_password debería ser permitida."
            )

        response_throttled = self.client.post(
            self.change_password_url,
            data=payload,
            format="json"
        )
        
        self.assertEqual(
            response_throttled.status_code,
            status.HTTP_429_TOO_MANY_REQUESTS,
            msg="La 4ª solicitud POST a change_password debería ser bloqueada."
        )

    def test_device_list_applies_user_rate_throttle(self):
        for i in range(3):
            response = self.client.get(self.devices_list_url, format="json")
            self.assertEqual(
                response.status_code,
                status.HTTP_200_OK,
                msg=f"La petición GET {i+1} a devices debería ser permitida."
            )

        response_throttled = self.client.get(self.devices_list_url, format="json")
        
        self.assertEqual(
            response_throttled.status_code,
            status.HTTP_429_TOO_MANY_REQUESTS,
            msg="La 4ª solicitud GET a devices debería ser bloqueada."
        )

    def test_different_endpoints_throttles_independent(self):
        for i in range(3):
            response = self.client.get(self.profile_url, format="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        for i in range(2):
            response = self.client.get(
                self.search_url,
                {"email": self.user2.email},
                format="json"
            )
            self.assertEqual(
                response.status_code,
                status.HTTP_200_OK,
                msg="Search debería funcionar aunque profile esté limitado."
            )

    def test_throttle_is_per_user(self):
        for i in range(3):
            response = self.client.get(self.profile_url, format="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=self.user2)
        
        for i in range(3):
            response = self.client.get(self.profile_url, format="json")
            self.assertEqual(
                response.status_code,
                status.HTTP_200_OK,
                msg=f"Usuario 2 debería poder hacer GET {i+1} sin limitación."
            )

    def test_throttle_response_includes_message(self):
        for i in range(2):
            self.client.get(
                self.search_url,
                {"email": self.user2.email},
                format="json"
            )

        response = self.client.get(
            self.search_url,
            {"email": self.user2.email},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn("detail", response.data)
        self.assertIn("búsquedas de usuarios", str(response.data["detail"]))