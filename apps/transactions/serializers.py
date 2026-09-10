from django.utils import timezone
from decimal import Decimal
from rest_framework import serializers
from apps.wallet.models import TransactionLimit
from .models import Transaction, Movement
from django.db.models import Sum

# listar movimientos contable
class MovementsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movement
        fields = [
            "id",
            "movement_type",
            "amount",
            "balance_before",
            "balance_after",
            "created_at",
        ]
        read_only_fields = fields


class TransactionDetailSerializer(serializers.ModelSerializer):
    movements = MovementsSerializer(many=True, read_only=True)
    sender_email = serializers.EmailField(
        source="wallet_from.user.email", read_only=True, default=None
    )
    receiver_email = serializers.EmailField(
        source="wallet_to.user.email", read_only=True, default=None
    )

    class Meta:
        model = Transaction
        fields = [
            "id",
            "transaction_type",
            "wallet_from",
            "wallet_to",
            "sender_email",
            "receiver_email",
            "amount",
            "status",
            "description",
            "ref_code",
            "created_at",
            "movements",
        ]
        read_only_fields = fields


# validar solicitud de transferencia
class TransferCreateSerializer(serializers.Serializer):
    receiver_wallet_id = serializers.UUIDField(
        help_text="UUID de la billetera de destino"
    )
    amount = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        min_value=Decimal("0.01"),
        help_text="Monto a transferir (debe ser mayor a 0)",
    )
    description = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        default="",
    )
    is_pre_blocked = serializers.BooleanField(required=False, default=False)



#validar recarga o deposito externo
class DepositCreateSerializer(serializers.Serializer):
    """
    Serializer de entrada para validar la recarga o depósito.
    """
    amount = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        min_value=Decimal("0.01"),
        help_text="Monto a recargar (debe ser mayor a 0)",
    )
    description = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        default="Depósito de fondos",
    )

class UserTransactionLimitSerializer(serializers.ModelSerializer):
    daily_spent = serializers.SerializerMethodField()
    daily_available = serializers.SerializerMethodField()
    monthly_spent = serializers.SerializerMethodField()
    monthly_available = serializers.SerializerMethodField()

    class Meta:
        model = TransactionLimit
        fields = [
            "daily_limit",
            "daily_spent",
            "daily_available",
            "monthly_limit",
            "monthly_spent",
            "monthly_available",
        ]

    def _get_daily_spent(self, user) -> Decimal:
        today = timezone.localdate()
        return (
            Transaction.objects.filter(
                wallet_from__user=user,
                transaction_type=Transaction.TransactionType.TRANSFER,
                status=Transaction.Status.COMPLETE,
                created_at__date=today,
            )
            .exclude(wallet_to__user=user)
            .aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )

    def _get_monthly_spent(self, user) -> Decimal:
        now = timezone.now()
        return (
            Transaction.objects.filter(
                wallet_from__user=user,
                transaction_type=Transaction.TransactionType.TRANSFER,
                status=Transaction.Status.COMPLETE, 
                created_at__year=now.year,
                created_at__month=now.month,
            )
            .exclude(wallet_to__user=user) 
            .aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )

    def get_daily_spent(self, obj)-> Decimal:
        return self._get_daily_spent(obj.user)

    def get_daily_available(self, obj) -> Decimal:
        if obj.daily_limit <= Decimal("0.00"):
            return Decimal("0.00")  
        spent = self._get_daily_spent(obj.user)
        return max(Decimal("0.00"), obj.daily_limit - spent)

    def get_monthly_spent(self, obj) -> Decimal:
        return self._get_monthly_spent(obj.user)

    def get_monthly_available(self, obj) -> Decimal:
        if obj.monthly_limit <= Decimal("0.00"):
            return Decimal("0.00")  
        spent = self._get_monthly_spent(obj.user)
        return max(Decimal("0.00"), obj.monthly_limit - spent)


class TransactionListSerializer(serializers.ModelSerializer):
    wallet_from_id = serializers.CharField(source="wallet_from.id", read_only=True, default=None)
    wallet_to_id = serializers.CharField(source="wallet_to.id", read_only=True, default=None)
    class Meta:
        model = Transaction
        fields = [
            "id",
            "ref_code",
            "transaction_type",
            "amount",
            "status",
            "wallet_from_id",
            "wallet_to_id",
            "description",
            "created_at",
        ]