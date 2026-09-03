from decimal import Decimal
from rest_framework import serializers
from apps.wallet.models import Wallet
from .models import Transaction, Movement


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
        readonly = True


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

    def validate_receiver_wallet_id(self, value):
        if not Wallet.objects.filter(id=value).exists():
            raise serializers.ValidationError("La billetera de destino no existe.")
        return value


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