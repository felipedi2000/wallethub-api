from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

@override_settings(SECRET_KEY="django-insecure-test-key-with-enough-length-32-bytes")
class AuthenticationViewsTestCase(APITestCase):

    def setUp(self):
        self.password = "StrongPass1234q@"
        
        self.existing_user = User.objects.create_user(
            email="test@test.com",
            password=self.password,
            first_name="Carlos",
            last_name="Pérez",
        )
        self.existing_user.refresh_from_db()

        self.register_url = "/api/v1/auth/register/"
        self.login_url = "/api/v1/auth/login/"
        self.me_url = "/api/v1/auth/me/"
        self.change_password_url = "/api/v1/auth/change-password/"
        self.update_user_url = "/api/v1/auth/me/"
        self.logout_url = "/api/v1/auth/logout/"
        self.devices_url = "/api/v1/auth/devices/"

    def test_register_user_success(self):
        payload = {
            "email": "newuser@test.com",
            "password": self.password,
            "password_confirm": self.password,
            "first_name": "Edison",
            "last_name": "León",
        }
        response = self.client.post(self.register_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email=payload["email"]).exists())

        if "password" in response.data:
            self.assertNotIn("password", response.data)

    def test_register_password_mismatch_fails(self):
        payload = {
            "email": "mismatch@test.com",
            "password": self.password,
            "password_confirm": "DifferentPass1234q@",
            "first_name": "Prueba",
            "last_name": "Fallback",
        }
        response = self.client.post(self.register_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_user_duplicate_email_fails(self):
        payload = {
            "email": "test@test.com",
            "password": self.password,
            "password_confirm": self.password,
            "first_name": "Otro",
            "last_name": "Nombre",
        }
        response = self.client.post(self.register_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_success_returns_tokens(self):
        payload = {
            "email": "test@test.com",
            "password": self.password,
        }
        response = self.client.post(self.login_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_invalid_password_fails(self):
        payload = {
            "email": "test@test.com",
            "password": "WrongPassword123!",
        }
        response = self.client.post(self.login_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_user_profile_me_success(self):
        self.client.force_authenticate(user=self.existing_user)

        response = self.client.get(self.me_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "test@test.com")
        self.assertEqual(response.data["first_name"], "Carlos")

    def test_get_user_profile_me_unauthenticated_fails(self):
        response = self.client.get(self.me_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_user_profile_success(self):
        self.client.force_authenticate(user=self.existing_user)

        payload = {
            "first_name": "Carlos Updated",
            "last_name": "Pérez Updated",
        }
        response = self.client.put(self.update_user_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.existing_user.refresh_from_db()
        self.assertEqual(self.existing_user.first_name, "Carlos Updated")
        self.assertEqual(self.existing_user.last_name, "Pérez Updated")

    def test_change_password_success(self):
        self.client.force_authenticate(user=self.existing_user)

        new_password = "NewStrongPass5678@"
        payload = {
            "old_password": self.password,
            "new_password": new_password,
            "confirm_new_password": new_password,
        }
        response = self.client.post(self.change_password_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.existing_user.refresh_from_db()
        self.assertTrue(self.existing_user.check_password(new_password))

    def test_logout_success(self):
        self.client.force_authenticate(user=self.existing_user)

        refresh_token = RefreshToken.for_user(self.existing_user)
        payload = {
            "refresh": str(refresh_token)
        }
        response = self.client.post(self.logout_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "Sesión cerrada correctamente.")

    def test_logout_invalid_token_fails(self):
        self.client.force_authenticate(user=self.existing_user)

        payload = {
            "refresh": "invalid_or_expired_token_string"
        }
        response = self.client.post(self.logout_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_devices_success(self):
        self.client.force_authenticate(user=self.existing_user)

        response = self.client.get(self.devices_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_register_device_success(self):
        self.client.force_authenticate(user=self.existing_user)

        payload = {
            "device_name": "Mi cel user 4"
        }
        response = self.client.post(self.devices_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["device_name"], "Mi cel user 4")

    def test_patch_update_device_success(self):
        self.client.force_authenticate(user=self.existing_user)

        # 1. Crear dispositivo
        create_res = self.client.post(
            self.devices_url, {"device_name": "Celular Inicial"}, format="json"
        )
        device_id = create_res.data["id"]

        # 2. Actualizar parcialmente (PATCH)
        update_url = f"{self.devices_url}{device_id}/"
        payload = {"device_name": "Celular Actualizado PATCH"}
        response = self.client.patch(update_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["device_name"], "Celular Actualizado PATCH")

    def test_put_update_device_success(self):
        self.client.force_authenticate(user=self.existing_user)

        # 1. Crear dispositivo
        create_res = self.client.post(
            self.devices_url, {"device_name": "Laptop Vieja"}, format="json"
        )
        device_id = create_res.data["id"]

        # 2. Actualizar completo (PUT)
        update_url = f"{self.devices_url}{device_id}/"
        payload = {"device_name": "Laptop Nueva PUT"}
        response = self.client.put(update_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["device_name"], "Laptop Nueva PUT")

    def test_delete_device_success(self):
        self.client.force_authenticate(user=self.existing_user)

        # 1. Crear dispositivo
        create_res = self.client.post(
            self.devices_url, {"device_name": "Tablet a eliminar"}, format="json"
        )
        device_id = create_res.data["id"]

        # 2. Eliminar (DELETE)
        delete_url = f"{self.devices_url}{device_id}/"
        response = self.client.delete(delete_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_devices_unauthenticated_fails(self):
        response = self.client.get(self.devices_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)