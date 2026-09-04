from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError
from apps.wallet.models import Wallet
from .models import Transaction, Movement

class TransactionService:
  @staticmethod
  @transaction.atomic
  def execute_transfer(
    *,
    sender_wallet: Wallet,
    receiver_wallet_id: str,
    amount: Decimal,
    description: str = ""
  )-> Transaction:
    """
      ejecuta transferencia de forma atomica
    """
    if amount <= 0:
      raise ValidationError("El monto debe ser mayor a cero.")

    if str(sender_wallet.id) == str(receiver_wallet_id):
      raise ValidationError("No puedes realizar una transferencia a tu propia billeter.")
    # ordenar id
    wallets_ids = sorted([str(sender_wallet.id), str(receiver_wallet_id)])

    wallets = (
      Wallet.objects.select_for_update()
      .filter(id__in=wallets_ids)
      .in_bulk() 
    )

    sender = wallets.get(sender_wallet.id)
    receiver = wallets.get(receiver_wallet_id)

    if not receiver:
      raise ValidationError("La billetera de destino no existe.")

    if sender.balance < amount:
      raise ValidationError("Saldo insuficiente para realizar la transferencia.")

    # crear transaccion
    txn = Transaction.objects.create(
      transaction_type = Transaction.TransactionType.TRANSFER,
      wallet_from = sender,
      wallet_to = receiver,
      amount = amount,
      status = Transaction.Status.COMPLETE,
      description=description
    )

    sender_balance_before = sender.balance
    sender.balance -= amount
    sender.save(update_fields=["balance"])

    # baalance de salida
    # dos movimientos a la misma transaccion
    Movement.objects.create(
      wallet=sender,
      transaction=txn,
      movement_type = Movement.MovementType.DEBIT,
      amount=amount,
      balance_before = sender_balance_before,
      balance_after = sender.balance,
    )

    # balance de entraa
    receiver_balance_before = receiver.balance
    receiver.balance += amount
    receiver.save(update_fields=["balance"])
    Movement.objects.create(
      wallet=receiver,
      transaction=txn,
      movement_type = Movement.MovementType.CREDIT,
      amount = amount,
      balance_before = receiver_balance_before,
      balance_after=receiver.balance
    )

    return txn

  @staticmethod
  @transaction.atomic #aseguramos roll back
  def execute_deposit(
        *,
        wallet: Wallet,
        amount: Decimal,
        description: str = "Depósito de fondos",
    ) -> Transaction:
        """
        depósito externo a una billetera.
        """
        if amount <= 0:
            raise ValidationError("El monto debe ser mayor a cero.")

        # Bloqueo exclusivo de la billetera destino
        locked_wallet = Wallet.objects.select_for_update().get(id=wallet.id)

        txn = Transaction.objects.create(
            transaction_type=Transaction.TransactionType.DEPOSIT,
            wallet_from=None,  # Origen externo
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