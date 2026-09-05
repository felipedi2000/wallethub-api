from rest_framework import serializers
from .models import TransactionLimit
from apps.wallet.models import Wallet

class TransactionLimitSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionLimit
        fields = [
            "id",
            "daily_limit",
            "monthly_limit",
            "daily_used",
            "monthly_used",
            "reset_date",
        ]
        # cleinte no puede editar estos valores en API API
        read_only_fields = fields


class WalletSerializer(serializers.ModelSerializer):
    available_balance = serializers.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        read_only=True
    )

    class Meta:
        model = Wallet
        fields = [
            "id",
            "balance",
            "blocked_balance",
            "available_balance",
            "currency",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields