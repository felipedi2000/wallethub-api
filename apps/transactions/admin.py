from django.contrib import admin
from .models import IdempotencyKey, Movement, Transaction

@admin.register(IdempotencyKey)
class IdempotencyKeyAdmin(admin.ModelAdmin):
    list_display = ("key", "user", "created_at")
    search_fields = ("key", "user__email")
    readonly_fields = ("created_at",)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "wallet_from", "wallet_to", "amount", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("id", "ref_code")
    readonly_fields = ("id", "created_at")


@admin.register(Movement)
class MovementAdmin(admin.ModelAdmin):
    list_display = ("id", "wallet", "transaction", "movement_type", "amount", "created_at")
    list_filter = ("movement_type", "created_at")
    search_fields = ("wallet__id", "transaction__id")
    readonly_fields = ("id", "created_at")