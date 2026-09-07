from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from apps.wallet.models import Wallet, TransactionLimit
from apps.transactions.models import Transaction
from apps.transactions.services import TransactionService

User = get_user_model()


class TransactionServiceTestCase(TestCase):

    def setUp(self):
        """
        1. ARRANGE: Crear usuarios en la BD de pruebas.
        Las señales post_save crean automáticamente la Wallet y TransactionLimit.
        """
        self.user_a = User.objects.create_user(
            first_name="Edison",
            last_name="León",
            email="edison@test.com",
            password="Password123!",
        )
        self.user_b = User.objects.create_user(
            first_name="Carlos",
            last_name="Pérez",
            email="carlos@test.com",
            password="Password123!",
        )

        # Cargar saldo en las billeteras generadas por la señal
        self.wallet_a1 = Wallet.objects.get(user=self.user_a)
        self.wallet_a1.balance = Decimal("10000000.00")
        self.wallet_a1.save()

        self.wallet_b = Wallet.objects.get(user=self.user_b)
        self.wallet_b.balance = Decimal("200000.00")
        self.wallet_b.save()

        # Configurar topes: $50,000 diario y $5,000,000 mensual
        limits_a = TransactionLimit.objects.get(user=self.user_a)
        limits_a.daily_limit = Decimal("50000.00")
        limits_a.monthly_limit = Decimal("5000000.00")
        limits_a.save()

    def test_execute_transfer_success(self):
        """Verifica transferencia exitosa pasando el UUID de la billetera destino."""
        monto = Decimal("30000.00")

        tx = TransactionService.execute_transfer(
            sender_wallet=self.wallet_a1,
            receiver_wallet_id=str(self.wallet_b.id),  # Se pasa el ID como string
            amount=monto,
            description="Pago exitoso",
        )

        self.wallet_a1.refresh_from_db()
        self.wallet_b.refresh_from_db()

        self.assertEqual(tx.status, Transaction.Status.COMPLETED)
        self.assertEqual(self.wallet_a1.balance, Decimal("9970000.00"))
        self.assertEqual(self.wallet_b.balance, Decimal("230000.00"))

    def test_execute_transfer_insufficient_balance(self):
        """Verifica que falle si el saldo es menor al monto solicitado."""
        self.wallet_a1.balance = Decimal("10000.00")
        self.wallet_a1.save()

        with self.assertRaises(ValidationError):
            TransactionService.execute_transfer(
                sender_wallet=self.wallet_a1,
                receiver_wallet_id=str(self.wallet_b.id),
                amount=Decimal("20000.00"),
            )

        self.wallet_a1.refresh_from_db()
        self.assertEqual(self.wallet_a1.balance, Decimal("10000.00"))

    def test_transfer_exceeds_daily_limit(self):
        """Verifica que falle si el monto o acumulado supera los $50,000 diarios."""
        # Intento directo de $60,000
        with self.assertRaises(ValidationError):
            TransactionService.execute_transfer(
                sender_wallet=self.wallet_a1,
                receiver_wallet_id=str(self.wallet_b.id),
                amount=Decimal("60000.00"),
            )

        # Primera transferencia válida de $40,000
        TransactionService.execute_transfer(
            sender_wallet=self.wallet_a1,
            receiver_wallet_id=str(self.wallet_b.id),
            amount=Decimal("40000.00"),
        )

        # Segunda transferencia de $20,000 (acumula $60,000 > tope de $50,000)
        with self.assertRaises(ValidationError):
            TransactionService.execute_transfer(
                sender_wallet=self.wallet_a1,
                receiver_wallet_id=str(self.wallet_b.id),
                amount=Decimal("20000.00"),
            )

    def test_transfer_exceeds_monthly_limit(self):
        """Verifica que falle si el acumulado mensual supera los $5,000,000."""
        limits = TransactionLimit.objects.get(user=self.user_a)
        limits.daily_limit = Decimal("6000000.00")
        limits.save()

        # Transferencia dentro del margen ($4,500,000)
        TransactionService.execute_transfer(
            sender_wallet=self.wallet_a1,
            receiver_wallet_id=str(self.wallet_b.id),
            amount=Decimal("4500000.00"),
        )

        # Exceso acumulado ($4.5M + $600k = $5.1M > $5M)
        with self.assertRaises(ValidationError):
            TransactionService.execute_transfer(
                sender_wallet=self.wallet_a1,
                receiver_wallet_id=str(self.wallet_b.id),
                amount=Decimal("600000.00"),
            )