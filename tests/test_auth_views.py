from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

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

    def test_register_user_success(self):
        payload = {
            "email": "newuser@test.com",
            "password": self.password,
            "first_name": "Edison",
            "last_name": "León",
        }
        response = self.client.post(self.register_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email=payload["email"]).exists())

        if "password" in response.data:
            self.assertNotIn("password", response.data)

    def test_register_user_duplicate_email_fails(self):
        payload = {
            "email": "test@test.com",
            "password": self.password,
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