from django.db.models.signals import post_save
from django.db import transaction
from django.dispatch import receiver
from django.conf import settings
from .models import TransactionLimit, Wallet

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_financial_profile(sender, instance, created, **kwargs):
    if created:
        transaction.on_commit(
            lambda: _initialize_financial_profile(instance)
        )

def _initialize_financial_profile(user):
    TransactionLimit.objects.get_or_create(
        user=user,
        defaults={
            "daily_limit": 50000.00,
            "monthly_limit": 500000.00,
            "daily_used": 0.00,
            "monthly_used": 0.00,
        },
    )

    Wallet.objects.get_or_create(
        user=user,
        defaults={
            "currency": Wallet.Currency.COP,
            "balance": 0.00,
            "blocked_balance": 0.00,
        },
    )