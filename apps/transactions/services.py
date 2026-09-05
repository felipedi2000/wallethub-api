from decimal import Decimal
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.wallet.models import Wallet
from apps.transactions.models import Transaction, Movement


class TransactionService:

    @staticmethod
    def _validate_user_limits(wallet: Wallet, amount: Decimal) -> None:
        """
        Valida dinámicamente que el monto no exceda los topes configurados.
        Calcula el consumo en tiempo real mediante agregación sobre Transaction.
        """
        limits = getattr(wallet.user, "transaction_limit", None)
        if not limits:
            return

        now = timezone.now()
        today = now.date()

        # 1. LÍMITE DIARIO
        if limits.daily_limit > Decimal("0.00"):
            daily_spent = Transaction.objects.filter(
                wallet_from=wallet,
                transaction_type=Transaction.TransactionType.TRANSFER,
                created_at__date=today,
            ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

            if (daily_spent + amount) > limits.daily_limit:
                available_daily = max(Decimal("0.00"), limits.daily_limit - daily_spent)
                raise ValidationError(
                    f"Límite diario superado. Disponible hoy: ${available_daily:,.2f} COP"
                )

        # 2. LÍMITE MENSUAL
        if limits.monthly_limit > Decimal("0.00"):
            monthly_spent = Transaction.objects.filter(
                wallet_from=wallet,
                transaction_type=Transaction.TransactionType.TRANSFER,
                created_at__year=now.year,
                created_at__month=now.month,
            ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

            if (monthly_spent + amount) > limits.monthly_limit:
                available_monthly = max(
                    Decimal("0.00"), limits.monthly_limit - monthly_spent
                )
                raise ValidationError(
                    f"Límite mensual superado. Disponible este mes: ${available_monthly:,.2f} COP"
                )

    @staticmethod
    @transaction.atomic
    def execute_transfer(
        *,
        sender_wallet: Wallet,
        receiver_wallet_id: str,
        amount: Decimal,
        description: str = "",
    ) -> Transaction:
        """
        Ejecuta la transferencia entre dos billeteras con seguridad ACID y partida doble.
        """
        if amount <= Decimal("0.00"):
            raise ValidationError("El monto debe ser mayor a cero.")

        if str(sender_wallet.id) == str(receiver_wallet_id):
            raise ValidationError("No puedes realizar una transferencia a tu propia billetera.")

        # Ordenar IDs para garantizar bloqueos consistentes
        wallet_ids = sorted([str(sender_wallet.id), str(receiver_wallet_id)])

        # Traer y bloquear ambas billeteras en 1 sola consulta SQL con JOINs
        wallets = (
            Wallet.objects.select_related("user", "user__transaction_limit")
            .filter(id__in=wallet_ids)
            .select_for_update()
            .in_bulk()
        )

        # Extraer usando string explícito o UUID según cómo in_bulk mapeó la clave
        sender = wallets.get(sender_wallet.id) or wallets.get(str(sender_wallet.id))
        receiver = wallets.get(receiver_wallet_id) or wallets.get(str(receiver_wallet_id))

        if not receiver:
            raise ValidationError("La billetera de destino no existe.")

        # 1. Validar límites de emisor
        TransactionService._validate_user_limits(wallet=sender, amount=amount)

        # 2. Validar saldo
        if sender.balance < amount:
            raise ValidationError("Saldo insuficiente para realizar la transferencia.")

        # 3. Crear encabezado de transacción
        txn = Transaction.objects.create(
            transaction_type=Transaction.TransactionType.TRANSFER,
            wallet_from=sender,
            wallet_to=receiver,
            amount=amount,
            status=Transaction.Status.COMPLETE,
            description=description,
        )

        # 4. Asentar Débito (Salida)
        sender_balance_before = sender.balance
        sender.balance -= amount
        sender.save(update_fields=["balance"])

        Movement.objects.create(
            wallet=sender,
            transaction=txn,
            movement_type=Movement.MovementType.DEBIT,
            amount=amount,
            balance_before=sender_balance_before,
            balance_after=sender.balance,
        )

        # 5. Asentar Crédito (Entrada)
        receiver_balance_before = receiver.balance
        receiver.balance += amount
        receiver.save(update_fields=["balance"])

        Movement.objects.create(
            wallet=receiver,
            transaction=txn,
            movement_type=Movement.MovementType.CREDIT,
            amount=amount,
            balance_before=receiver_balance_before,
            balance_after=receiver.balance,
        )

        return txn

    @staticmethod
    @transaction.atomic
    def execute_deposit(
        *,
        wallet: Wallet,
        amount: Decimal,
        description: str = "Depósito de fondos",
    ) -> Transaction:
        """
        Ejecuta la recarga externa de fondos.
        """
        if amount <= Decimal("0.00"):
            raise ValidationError("El monto debe ser mayor a cero.")

        locked_wallet = Wallet.objects.select_for_update().get(id=wallet.id)

        txn = Transaction.objects.create(
            transaction_type=Transaction.TransactionType.DEPOSIT,
            wallet_from=None,
            wallet_to=locked_wallet,
            amount=amount,
            status=Transaction.Status.COMPLETE,
            description=description,
        )

        balance_before = locked_wallet.balance
        locked_wallet.balance += amount
        locked_wallet.save(update_fields=["balance"])

        Movement.objects.create(
            wallet=locked_wallet,
            transaction=txn,
            movement_type=Movement.MovementType.CREDIT,
            amount=amount,
            balance_before=balance_before,
            balance_after=locked_wallet.balance,
        )

        return txn