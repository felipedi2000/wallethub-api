from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APITestCase
from apps.wallet.models import Wallet
from apps.shared.throttles import CustomUserRateThrottle

User = get_user_model()


class UserWalletThrottlingTestCase(APITestCase):

    def setUp(self):
        cache.clear()

        CustomUserRateThrottle.rate = "3/minute"

        self.user = User.objects.create_user(
            first_name="usuario1",
            last_name="apellido1",
            email="wallet@test.com",
            password="Password123!",
        )

        self.wallet = Wallet.objects.get(user=self.user)
        self.wallet.balance = Decimal("5000.00")
        self.wallet.save()

        self.user.refresh_from_db()

        self.client.force_authenticate(user=self.user)
        self.wallet_url = "/api/v1/wallet/me/"

    def tearDown(self):
        cache.clear()

    def test_user_wallet_view_applies_user_rate_throttle(self):
        for i in range(3):
            response = self.client.get(self.wallet_url, format="json")
            self.assertEqual(
                response.status_code,
                status.HTTP_200_OK,
                msg=f"La petición GET {i+1} a wallet/me debería ser permitida."
            )
            self.assertIn("balance", response.data)
            self.assertEqual(
                Decimal(str(response.data["balance"])),
                Decimal("5000.00")
            )

        response_throttled = self.client.get(self.wallet_url, format="json")
        self.assertEqual(
            response_throttled.status_code,
            status.HTTP_429_TOO_MANY_REQUESTS,
            msg="La 4ª solicitud GET a wallet/me debería ser bloqueada."
        )
        self.assertIn("detail", response_throttled.data)

    def test_user_wallet_throttle_is_per_user(self):
        for i in range(3):
            response = self.client.get(self.wallet_url, format="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        user2 = User.objects.create_user(
            first_name="usuario2",
            last_name="apellido2",
            email="wallet2@test.com",
            password="Password123!",
        )
        wallet2 = Wallet.objects.get(user=user2)
        wallet2.balance = Decimal("1000.00")
        wallet2.save()

        user2.refresh_from_db()
        self.client.force_authenticate(user=user2)

        for i in range(3):
            response = self.client.get(self.wallet_url, format="json")
            self.assertEqual(
                response.status_code,
                status.HTTP_200_OK,
                msg=f"Usuario 2 debería poder hacer GET {i+1} sin limitación."
            )
            self.assertEqual(
                Decimal(str(response.data["balance"])),
                Decimal("1000.00")
            )

    def test_user_wallet_requires_authentication(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.wallet_url, format="json")

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
            msg="Sin autenticación debería devolver 401."
        )

    def test_user_wallet_returns_correct_balance(self):
        response = self.client.get(self.wallet_url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            Decimal(str(response.data["balance"])),
            Decimal("5000.00")
        )

        self.assertEqual(str(response.data["id"]), str(self.wallet.id))