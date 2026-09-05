from decimal import Decimal
import uuid
from django.conf import settings
from django.db import models

class Wallet(models.Model):
    class Currency(models.TextChoices):
        COP = "COP", "Peso Colombiano"
        USD = "USD", "Dólar Estadounidense"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wallet",
    )
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    blocked_balance = models.DecimalField(
        max_digits=15, decimal_places=2, default=0.00
    )
    currency = models.CharField(
        max_length=3, choices=Currency.choices, default=Currency.COP
    ) 
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def available_balance(self) -> Decimal:
        """Calcula el saldo disponible excluyendo retenciones o bloqueos."""
        return self.balance - self.blocked_balance
    
    def __str__(self):
        return f"Wallet {self.user} - {self.balance} {self.currency}"

class TransactionLimit(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="transaction_limit",
    )
    daily_limit = models.DecimalField(max_digits=15, decimal_places=2, default=0.0)
    monthly_limit = models.DecimalField(max_digits=15, decimal_places=2, default=0.0)
    
    def __str__(self):
        return f"Limites de {self.user}"
