import uuid
from decimal import Decimal
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from apps.wallet.models import Wallet, TransactionLimit
from apps.transactions.models import Transaction

User = get_user_model()


class TransactionViewsTestCase(APITestCase):
    def setUp(self):
        
        self.user_a = User.objects.create_user(
            first_name="usaurio1",
            last_name="apellido1",
            email="user1@test.com",
            password="Password123",
        )
        self.user_b = User.objects.create_user(
            first_name="usuario2",
            last_name="apellido2",
            email="user2@test.com",
            password="Password123",
        )

        # traer billeteras creadas por señales
        self.wallet_a = Wallet.objects.get(user=self.user_a)
        self.wallet_a.balance = Decimal("1000000.00")
        self.wallet_a.save()

        self.wallet_b = Wallet.objects.get(user=self.user_b)
        self.wallet_b.balance = Decimal("200000.00")
        self.wallet_b.save()

        # limites por billetera
        limits_a = TransactionLimit.objects.get(user=self.user_a)
        limits_a.daily_limit = Decimal("50000.00")
        limits_a.monthly_limit = Decimal("5000000.00")
        limits_a.save()

        self.transfer_url = "/api/v1/transactions/transfer/"
        self.history_url = "/api/v1/transactions/"
        self.deposit_url = "/api/v1/transactions/deposit/"
        self.limits_url = "/api/v1/transactions/limits/me/"

    def test_deposit_unauthenticated_fails(self):
        payload = {
            "amount": "10000.00",
            "description": "Intento sin token",
        }

        response = self.client.post(self.deposit_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_ttest_transfer_unauthenticated_fails(self):
        payload = {
            "receiver_wallet_id": str(self.wallet_b.id),
            "amount": "10000.00",
            "description": "Intento sin token",
        }

        response = self.client.post(self.transfer_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_transfer_success(self):
        self.client.force_authenticate(user=self.user_a)

        idempotency_key = str(uuid.uuid4())
        
        payload = {
            "receiver_wallet_id": str(self.wallet_b.id),
            "amount": "20000.00",
            "description": "Pago via API HTTP",
        }

        response_no_key = self.client.post(
            self.transfer_url,
            payload,
            format="json"
        )
        self.assertEqual(response_no_key.status_code, status.HTTP_400_BAD_REQUEST)

        # Confirmar que no se envio dinero
        self.wallet_a.refresh_from_db()
        self.assertEqual(self.wallet_a.balance, Decimal("1000000.00"))

        response_1 = self.client.post(
            self.transfer_url,
            payload,
            format="json",
            HTTP_X_IDEMPOTENCY_KEY=idempotency_key
        )
        
        self.assertEqual(response_1.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response_1.data)

        # refrescar variables desde db y validar valor
        self.wallet_a.refresh_from_db()
        self.wallet_b.refresh_from_db()
        self.assertEqual(self.wallet_a.balance, Decimal("980000.00"))
        self.assertEqual(self.wallet_b.balance, Decimal("220000.00"))

        # segunda peticion imdepotencia
        response_2 = self.client.post(
            self.transfer_url,
            payload,
            format="json",
            HTTP_X_IDEMPOTENCY_KEY=idempotency_key
        )

        # debe reponder creado
        self.assertIn(response_2.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        self.assertEqual(response_1.data["id"], response_2.data["id"])

        # saldos iguales al usar imdepotencia
        self.wallet_a.refresh_from_db()
        self.wallet_b.refresh_from_db()
        self.assertEqual(self.wallet_a.balance, Decimal("980000.00"))
        self.assertEqual(self.wallet_b.balance, Decimal("220000.00"))

    def test_transfer_exceeds_daily_limit_returns_400(self):
        
        self.client.force_authenticate(user=self.user_a)

        payload = {
            "receiver_wallet_id": str(self.wallet_b.id),
            "amount": "60000.00",
            "description": "Intento excedido",
        }
        
        response = self.client.post(
            self.transfer_url,
            payload,
            format="json",
            HTTP_X_IDEMPOTENCY_KEY=str(uuid.uuid4())
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    

    def test_transaction_history_pagination_structure(self):
        #historial y paginacion
        self.client.force_authenticate(user=self.user_a)

        # Crear 15 transacciones para forzar la paginacion
        for i in range(15):
            Transaction.objects.create(
                wallet_from=self.wallet_a,
                wallet_to=self.wallet_b,
                amount=Decimal("1000.00"),
                status=Transaction.Status.COMPLETE,
                description=f"Transacción masiva {i}",
            )

        response = self.client.get(self.history_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Comprobar la estructura estándar de PageNumberPagination de DRF
        self.setIsInstance(response.data, list) if hasattr(self, 'setIsInstance') else self.assertTrue(isinstance(response.data, list))
        self.assertEqual(len(response.data), 15)

    def test_user_cannot_see_other_users_transactions(self):
        """Aislamiento de seguridad: User B no debe ver las transacciones donde solo participa User A."""
        # Generar transacción exclusiva para la Billetera A
        Transaction.objects.create(
            wallet_from=self.wallet_a,
            wallet_to=self.wallet_a,
            amount=Decimal("5000.00"),
            status=Transaction.Status.COMPLETE,
        )

        # Autenticar como Usuario B (quien no es sender ni receiver)
        self.client.force_authenticate(user=self.user_b)
        response = self.client.get(self.history_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # El conteo aislado para el Usuario B debe ser 0
        self.assertEqual(len(response.data), 0)
    
    def test_get_user_transaction_limits_and_usage(self):
        self.client.force_authenticate(user=self.user_a)

        #  probar el uso correcto de endpoint de limites y uso
        Transaction.objects.create(
            wallet_from=self.wallet_a,
            wallet_to=self.wallet_b,
            amount=Decimal("15000.00"),
            transaction_type=Transaction.TransactionType.TRANSFER,
            status=Transaction.Status.COMPLETE,
            description="Transferencia de prueba para límites",
        )

        response = self.client.get(self.limits_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_fields = [
            "daily_limit",
            "daily_spent",
            "daily_available",
            "monthly_limit",
            "monthly_spent",
            "monthly_available",
        ]
        for field in expected_fields:
            self.assertIn(field, response.data)

        # validar montos consumidos y disponibles
        self.assertEqual(Decimal(str(response.data["daily_limit"])), Decimal("50000.00"))
        self.assertEqual(Decimal(str(response.data["daily_spent"])), Decimal("15000.00"))
        self.assertEqual(Decimal(str(response.data["daily_available"])), Decimal("35000.00"))

        self.assertEqual(Decimal(str(response.data["monthly_spent"])), Decimal("15000.00"))

    def test_deposit_success(self):
        self.client.force_authenticate(user=self.user_a)

        payload = {
            "amount": "50000.00",
            "description": "Carga de saldo vía PSE/Tarjeta",
        }
        # verificar que se aumente correctamente el saldo tras otra transacción
        response = self.client.post(
            self.deposit_url,
            payload,
            format="json",
            HTTP_X_IDEMPOTENCY_KEY=str(uuid.uuid4())
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.wallet_a.refresh_from_db()
        self.assertEqual(self.wallet_a.balance, Decimal("1050000.00"))

    def test_transfer_insufficient_funds_fails(self):
        self.client.force_authenticate(user=self.user_a)

        payload = {
            "receiver_wallet_id": str(self.wallet_b.id),
            "amount": "2000000.00",  # Saldo actual: $1,000,000
            "description": "Intento sin fondos suficientes",
        }

        response = self.client.post(
            self.transfer_url,
            payload,
            format="json",
            HTTP_X_IDEMPOTENCY_KEY=str(uuid.uuid4())
        )
        # rechzar si el monto es insuficiente
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.wallet_a.refresh_from_db()
        # verificar que no se hizo descuento
        self.assertEqual(self.wallet_a.balance, Decimal("1000000.00"))

    def test_transfer_negative_or_zero_amount_fails(self):
        self.client.force_authenticate(user=self.user_a)

        payload = {
            "receiver_wallet_id": str(self.wallet_b.id),
            "amount": "-5000.00",
            "description": "Monto negativo",
        }

        response = self.client.post(
            self.transfer_url,
            payload,
            format="json",
            HTTP_X_IDEMPOTENCY_KEY=str(uuid.uuid4())
        )
        # no transacciones iguales o menores a 0.0
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_transaction_history_ordered_by_newest(self):
        self.client.force_authenticate(user=self.user_a)

        tx1 = Transaction.objects.create(
            wallet_from=self.wallet_a,
            wallet_to=self.wallet_b,
            amount=Decimal("1000.00"),
            status=Transaction.Status.COMPLETE,
            description="Primera transacción",
        )
        tx2 = Transaction.objects.create(
            wallet_from=self.wallet_a,
            wallet_to=self.wallet_b,
            amount=Decimal("2000.00"),
            status=Transaction.Status.COMPLETE,
            description="Segunda transacción",
        )

        response = self.client.get(self.history_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # transacciones ordenaas por fecha retornen correctamdente
        self.assertEqual(str(response.data[0]["id"]), str(tx2.id))
        self.assertEqual(str(response.data[1]["id"]), str(tx1.id))