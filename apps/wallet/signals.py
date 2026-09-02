from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import TransactionLimit, Wallet

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_financial_profile(sender, instance, created, **kwargs):
    if created:
        TransactionLimit.objects.create(
            user=instance,
            daily_limit=50000.00,
            monthly_limit=500000.00,
            daily_used=0.00,
            monthly_used=0.00
        )

        Wallet.objects.create(
            user=instance,
            currency=Wallet.Currency.COP,
            balance=0.00,
            blocked_balance=0.00
        )