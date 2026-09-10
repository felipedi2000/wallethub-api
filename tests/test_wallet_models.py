from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from apps.wallet.models import Wallet

User = get_user_model()


class WalletModelTestCase(TestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(
            email="wallet.model@example.com",
            password="SecurePassword123",
            first_name="Model",
            last_name="Test",
        )

    def test_wallet_creation_and_defaults(self):
        wallet = Wallet.objects.get(user=self.user_a)
        self.assertEqual(wallet.user, self.user_a)
        self.assertEqual(wallet.balance, Decimal("0.00"))

    def test_wallet_unique_user_constraint(self):
        with self.assertRaises(IntegrityError):
            Wallet.objects.create(user=self.user_a, balance=Decimal("100.00"))

    def test_wallet_str_representation(self):
        wallet = Wallet.objects.get(user=self.user_a)
        expected_str = f"Wallet {self.user_a} - {wallet.balance} {wallet.currency}"
        self.assertEqual(str(wallet), expected_str)