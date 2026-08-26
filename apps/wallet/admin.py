from django.contrib import admin
from .models import Wallet, TransactionLimit


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "balance", "currency", "created_at")
    list_filter = ("currency",)
    search_fields = ("user__email", "id")
    readonly_fields = ("id", "created_at", "updated_at")

@admin.register(TransactionLimit)
class TransactionLimitAdmin(admin.ModelAdmin):
    list_display = ("user", "daily_limit", "monthly_limit", "daily_used", "monthly_used")
    search_fields = ("user__email",)
