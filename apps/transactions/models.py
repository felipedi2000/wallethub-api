from decimal import Decimal
import uuid
from django.conf import settings
from django.db import models
from apps.wallet.models import Wallet
from apps.authentication.models import Device
import uuid
from django.conf import settings
from django.db import models


class IdempotencyKey(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="idempotency_keys",
    )
    key = models.CharField(max_length=255)
    
    response_code = models.PositiveIntegerField(null=True, blank=True)
    response_data = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "idempotency_keys"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "key"], name="unique_user_idempotency_key"
            )
        ]

    def __str__(self):
        return f"IdempotencyKey {self.key} - {self.user}"


class Transaction(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pendiente"
        COMPLETE = "COMPLETE", "Completada"
        FAILED = "FAILED", "Fallida"

    class TransactionType(models.TextChoices):
        DEPOSIT = "DEPOSIT", "Depósito"
        WITHDRAWAL = "WITHDRAWAL", "Retiro"
        TRANSFER = "TRANSFER", "Transferencia"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    transaction_type = models.CharField(
        max_length=15, choices=TransactionType.choices
    )

    # evitar que si se borra una cartera se pierda el historial
    wallet_from = models.ForeignKey(
        Wallet,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="sent_transactions",  
    )

    wallet_to = models.ForeignKey(
        Wallet,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="received_transactions", 
    )

    amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal("0.00")
    )

    status = models.CharField(
        max_length=15, choices=Status.choices, default=Status.PENDING
    )

    description = models.CharField(max_length=255, blank=True, default="")
    ref_code = models.CharField(max_length=100, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    aupdated_at = models.DateTimeField(auto_now_add=True)
    # --- auditoria dispositivo ---
    device = models.ForeignKey(
        Device,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
        help_text="Dispositivo desde el cual se autorizó la transacción",
    )

    ip_address = models.GenericIPAddressField(
        null=True, blank=True, help_text="IP origen de la petición HTTP"
    )

    user_agent = models.TextField(
        blank=True, default="", help_text="Información del cliente (Navegador/App)"
    )

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                check=models.Q(amount__gt=0),
                name="transaction_amount_must_be_positive",
            )
        ]
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['wallet_from', '-created_at']),
            models.Index(fields=['wallet_to', '-created_at']),
        ]

    def __str__(self):
        return f"Transacción {self.id} | {self.amount} | {self.status}"
    
class Movement(models.Model):
    class MovementType(models.TextChoices):
        CREDIT = "CREDIT", "Crédito (Entrada +)"
        DEBIT = "DEBIT", "Débito (Salida -)"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # A que billetera afecto este movimiento
    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.PROTECT,
        related_name="movements",
    )

    # A que transaccion global pertenece este movimiento
    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.PROTECT,
        related_name="movements",
    )

    movement_type = models.CharField(
        max_length=10,
        choices=MovementType.choices,
    )

    amount = models.DecimalField(max_digits=15, decimal_places=2)

    # Captura de adutoria: saldo justo antes y justo después del movimiento
    balance_before = models.DecimalField(max_digits=15, decimal_places=2)
    balance_after = models.DecimalField(max_digits=15, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.movement_type} ${self.amount} -> Wallet {self.wallet_id}"
