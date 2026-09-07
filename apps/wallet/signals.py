from decimal import Decimal

from django.db.models.signals import post_save
from django.db import transaction
from django.dispatch import receiver
from django.conf import settings
from .models import TransactionLimit, Wallet

# signals.py
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_financial_profile(sender, instance, created, **kwargs):
    if created:
        TransactionLimit.objects.get_or_create(
            user=instance,
            defaults={
                "daily_limit": Decimal("50000.00"),
                "monthly_limit": Decimal("500000.00"),
            },
        )

        Wallet.objects.get_or_create(
            user=instance,
            defaults={
                "currency": Wallet.Currency.COP,
                "balance": Decimal("0.00"),
                "blocked_balance": Decimal("0.00"),
            },
        )