import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import UserManager


class User(AbstractUser):
    """
    Modelo de usuario personalizado para WalletHub.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None  # Desactiva el campo 'username' nativo
    email = models.EmailField("Email address", unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    first_name = models.CharField(max_length=20, blank=True)
    last_name = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  # No pide username al crear superusuario

    objects = UserManager()

    def __str__(self):
        return self.email


class Device(models.Model):
    """
    Gestión y auditoría de dispositivos asociados al usuario.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="devices")
    device_name = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    is_trusted = models.BooleanField(default=False)
    last_login_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.device_name}"
