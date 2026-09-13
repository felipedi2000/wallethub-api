from decimal import Decimal
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.wallet.models import Wallet
from apps.transactions.models import Transaction
from apps.shared.throttles import TransactionThrottle, CustomUserRateThrottle

User = get_user_model()

class TransactionThrottlingTestCase(APITestCase):

    def setUp(self):
        cache.clear()

        TransactionThrottle.rate = "2/minute"
        CustomUserRateThrottle.rate = "3/minute"
        self.sender = User.objects.create_user(
            first_name="usuario1",
            last_name="apellido1",
            email="sender@test.com",
            password="Password123!",
        )
        self.receiver = User.objects.create_user(
            first_name="usuario2",
            last_name="apellido2",
            email="receiver@test.com",
            password="Password123!",
        )

        self.sender_wallet = Wallet.objects.get(user=self.sender)
        self.sender_wallet.balance = Decimal("1000000.00")
        self.sender_wallet.save()

        self.receiver_wallet = Wallet.objects.get(user=self.receiver)
        self.receiver_wallet.balance = Decimal("200000.00")
        self.receiver_wallet.save()

        self.transaction = Transaction.objects.create(
            wallet_from=self.sender_wallet,
            wallet_to=self.receiver_wallet,
            amount=Decimal("100.00"),
        )

        self.client.force_authenticate(user=self.sender)

        self.transfer_url = "/api/v1/transactions/transfer/"
        self.deposit_url = "/api/v1/transactions/deposit/"
        self.list_url = "/api/v1/transactions/"
        self.retrieve_url = f"/api/v1/transactions/{self.transaction.id}/"
        self.history_url = "/api/v1/transactions/"
        self.limits_url = "/api/v1/transactions/limits/me/"

    def tearDown(self):
        cache.clear()

    def test_transfer_action_applies_transaction_throttle(self):
        payload = {
            "receiver_wallet_id": str(self.receiver_wallet.id),
            "amount": "10000.00",
            "description": "Prueba throttling transfer",
        }

        for i in range(2):
            response = self.client.post(
                self.transfer_url,
                data=payload,
                format="json",
                HTTP_X_IDEMPOTENCY_KEY=f"key-transfer-throttle-{i}",
            )
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                msg=f"La petición {i+1} debería ser permitida.",
            )

        response_throttled = self.client.post(
            self.transfer_url,
            data=payload,
            format="json",
            HTTP_X_IDEMPOTENCY_KEY="key-transfer-throttle-exceeded",
        )

        self.assertEqual(
            response_throttled.status_code, 
            status.HTTP_429_TOO_MANY_REQUESTS,
            msg="La 3ª solicitud debería ser bloqueada por throttle."
        )
        self.assertIn("detail", response_throttled.data)

    def test_deposit_action_applies_transaction_throttle(self):
        payload = {
            "amount": "50000.00",
            "description": "Prueba throttling deposit",
        }

        for i in range(2):
            response = self.client.post(
                self.deposit_url,
                data=payload,
                format="json",
                HTTP_X_IDEMPOTENCY_KEY=f"key-deposit-throttle-{i}",
            )
            self.assertEqual(
                response.status_code, 
                status.HTTP_201_CREATED,
                msg=f"La petición {i+1} debería ser permitida."
            )

        response_throttled = self.client.post(
            self.deposit_url,
            data=payload,
            format="json",
            HTTP_X_IDEMPOTENCY_KEY="key-deposit-throttle-exceeded",
        )
        
        self.assertEqual(
            response_throttled.status_code, 
            status.HTTP_429_TOO_MANY_REQUESTS,
            msg="La 3ª solicitud debería ser bloqueada por throttle."
        )

    def test_list_action_applies_user_rate_throttle(self):
        for i in range(3):
            response = self.client.get(self.list_url, format="json")
            self.assertEqual(
                response.status_code, 
                status.HTTP_200_OK,
                msg=f"La petición GET {i+1} debería ser permitida."
            )

        response_throttled = self.client.get(self.list_url, format="json")
        
        self.assertEqual(
            response_throttled.status_code, 
            status.HTTP_429_TOO_MANY_REQUESTS,
            msg="La 4ª solicitud GET debería ser bloqueada por throttle."
        )
        self.assertIn("detail", response_throttled.data)

    def test_retrieve_action_applies_user_rate_throttle(self):
        for i in range(3):
            response = self.client.get(self.retrieve_url, format="json")
            self.assertEqual(
                response.status_code, 
                status.HTTP_200_OK,
                msg=f"La petición GET retrieve {i+1} debería ser permitida."
            )

        response_throttled = self.client.get(self.retrieve_url, format="json")
        
        self.assertEqual(
            response_throttled.status_code, 
            status.HTTP_429_TOO_MANY_REQUESTS,
            msg="La 4ª solicitud GET retrieve debería ser bloqueada."
        )

    def test_transfer_and_deposit_share_same_throttle(self):
        transfer_payload = {
            "receiver_wallet_id": str(self.receiver_wallet.id),
            "amount": "1000.00",
        }
        deposit_payload = {
            "amount": "1000.00",
        }

        # 1 transfer permitida
        response1 = self.client.post(
            self.transfer_url,
            data=transfer_payload,
            format="json",
            HTTP_X_IDEMPOTENCY_KEY="key-combo-1",
        )
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        response2 = self.client.post(
            self.deposit_url,
            data=deposit_payload,
            format="json",
            HTTP_X_IDEMPOTENCY_KEY="key-combo-2",
        )
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)

        response3 = self.client.post(
            self.transfer_url,
            data=transfer_payload,
            format="json",
            HTTP_X_IDEMPOTENCY_KEY="key-combo-3",
        )
        self.assertEqual(
            response3.status_code, 
            status.HTTP_429_TOO_MANY_REQUESTS
        )

    def test_list_and_retrieve_share_same_throttle(self):
        response1 = self.client.get(self.list_url, format="json")
        self.assertEqual(response1.status_code, status.HTTP_200_OK)

        response2 = self.client.get(self.retrieve_url, format="json")
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        response3 = self.client.get(self.list_url, format="json")
        self.assertEqual(response3.status_code, status.HTTP_200_OK)

        response4 = self.client.get(self.retrieve_url, format="json")
        self.assertEqual(
            response4.status_code, 
            status.HTTP_429_TOO_MANY_REQUESTS
        )

    def test_different_throttles_independent(self):
        transfer_payload = {
            "receiver_wallet_id": str(self.receiver_wallet.id),
            "amount": "1000.00",
        }

        for i in range(2):
            response = self.client.post(
                self.transfer_url,
                data=transfer_payload,
                format="json",
                HTTP_X_IDEMPOTENCY_KEY=f"key-indep-{i}",
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response_list = self.client.get(self.list_url, format="json")
        self.assertEqual(
            response_list.status_code, 
            status.HTTP_200_OK,
            msg="GET list debería funcionar aunque transfer esté limitado."
        )

    
    def test_throttle_response_includes_wait_time(self):
        payload = {
            "receiver_wallet_id": str(self.receiver_wallet.id),
            "amount": "1000.00",
        }

        for i in range(2):
            self.client.post(
                self.transfer_url,
                data=payload,
                format="json",
                HTTP_X_IDEMPOTENCY_KEY=f"key-wait-{i}",
            )

        response = self.client.post(
            self.transfer_url,
            data=payload,
            format="json",
            HTTP_X_IDEMPOTENCY_KEY="key-wait-exceeded",
        )

        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn("detail", response.data)
        self.assertIn("Has superado el límite", str(response.data["detail"]))

    
    def test_throttle_is_per_user(self):
        payload1 = {
            "receiver_wallet_id": str(self.receiver_wallet.id),
            "amount": "1000.00",
        }
        
        for i in range(2):
            response = self.client.post(
                self.transfer_url,
                data=payload1,
                format="json",
                HTTP_X_IDEMPOTENCY_KEY=f"key-user1-{i}",
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.client.force_authenticate(user=self.receiver)
        
        payload2 = {
            "receiver_wallet_id": str(self.sender_wallet.id),
            "amount": "500.00",
        }
        
        for i in range(2):
            response = self.client.post(
                self.transfer_url,
                data=payload2,
                format="json",
                HTTP_X_IDEMPOTENCY_KEY=f"key-user2-{i}",
            )
            self.assertEqual(
                response.status_code, 
                status.HTTP_201_CREATED,
                msg=f"Usuario 2 deberia poder hacer transfer {i+1} sin limitación."
            )

    def test_user_limits_me_applies_user_rate_throttle(self):
      for i in range(3):
          response = self.client.get(self.limits_url, format="json")
          self.assertEqual(
              response.status_code, 
              status.HTTP_200_OK,
              msg=f"La petición GET {i+1} a user-limits debería ser permitida."
          )

      response_throttled = self.client.get(self.limits_url, format="json")
      
      self.assertEqual(
          response_throttled.status_code, 
          status.HTTP_429_TOO_MANY_REQUESTS,
          msg="La 4ª solicitud GET a user-limits debería ser bloqueada por throttle."
      )
      self.assertIn("detail", response_throttled.data)

    def test_transaction_history_applies_user_rate_throttle(self):
      params = {"page": 1, "page_size": 10}
      for i in range(3):
          response = self.client.get(self.history_url, params, format="json")
         
          self.assertEqual(
              response.status_code, 
              status.HTTP_200_OK,
              msg=f"La petición GET {i+1} a transaction-history debería ser permitida."
          )

      response_throttled = self.client.get(self.history_url, format="json")
      
      self.assertEqual(
          response_throttled.status_code, 
          status.HTTP_429_TOO_MANY_REQUESTS,
          msg="La 4ª solicitud GET a transaction-history debería ser bloqueada por throttle."
      )
      self.assertIn("detail", response_throttled.data)