from decimal import Decimal
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from apps.wallet.models import Wallet

User = get_user_model()

class WalletViewsTestCase(APITestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(
            email="wallet@example.com",
            password="Password123!",
            first_name="Wallet",
            last_name="Owner",
        )
        self.user_b = User.objects.create_user(
            email="other@example.com",
            password="Password123!",
            first_name="Other",
            last_name="User",
        )

        self.wallet_a = Wallet.objects.get(user=self.user_a)
        self.wallet_a.balance = Decimal("250000.50")
        self.wallet_a.save()

       
        self.user_a.refresh_from_db()

        self.wallet_b = Wallet.objects.get(user=self.user_b)
        self.wallet_b.balance = Decimal("0.00")
        self.wallet_b.save()
        self.user_b.refresh_from_db()

        self.wallet_url = "/api/v1/wallet/me/"

    def test_get_my_wallet_unauthenticated_fails(self):
        response = self.client.get(self.wallet_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_my_wallet_success(self):
        self.client.force_authenticate(user=self.user_a)

        response = self.client.get(self.wallet_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(response.data["id"]), str(self.wallet_a.id))
        self.assertEqual(Decimal(str(response.data["balance"])), Decimal("250000.50"))

    def test_user_cannot_see_other_user_wallet(self):
        """Garantiza que cada usuario consulte únicamente su propia billetera."""
        self.client.force_authenticate(user=self.user_b)

        response = self.client.get(self.wallet_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(str(response.data["id"]), str(self.wallet_a.id))
        self.assertEqual(Decimal(str(response.data["balance"])), Decimal("0.00"))