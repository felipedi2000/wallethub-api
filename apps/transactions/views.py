from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Transaction
from .serializers import (
    DepositCreateSerializer,
    TransactionDetailSerializer,
    TransferCreateSerializer,
)
from .services import TransactionService


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):

  permissions_clases = [IsAuthenticated]

  def get_queryset(self):

    user_wallet = self.user.wallet

    return(
      Transaction.objects.filter(wallet_from=user_wallet)
      | Transaction.objects.filter(wallet_to=user_wallet)
    ).distinct().select_related("wallet_from", "wallet_to").prefetch_related("movements")

  # serializer clase se define ya que no se pasa
  def get_serializer_class(self):
    if self.action == "transfer":
      return TransferCreateSerializer
    if self.action == "deposit":
      return DepositCreateSerializer
    return TransactionDetailSerializer

  # se agregan meotods post para transferencias a los meotods base de viwe set
  @action(detail=False, methods=["post"], url_path="ttransfer")
  def transfer(self, request):
    """
      POST /api/v1/transactions/transfer/
    """
    serializer = self.get_serializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
      transaction_obj = TransactionService.execute_transfer(
        sender_wallet=request.user.wallet,
        receiver_wallet_id=serializer.validated_data["receiver_wallet_id"],
        amount=serializer.validated_data.get("description", ""),
      )
    except DjangoValidationError as e:
      raise DRFValidationError(e.message)

    response_serializer = TransactionDetailSerializer(transaction_obj)
    return Response(response_serializer.data, status=status.HTTP_201_CREATED)

  @action(detail=False, methods=["post"], url_path="deposit")
  def deposit(self, request):
        """
        POST /api/v1/transactions/deposit/
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            transaction_obj = TransactionService.execute_deposit(
                wallet=request.user.wallet,
                amount=serializer.validated_data["amount"],
                description=serializer.validated_data.get("description", "Depósito de fondos"),
            )
        except DjangoValidationError as e:
            raise DRFValidationError(e.messages)

        response_serializer = TransactionDetailSerializer(transaction_obj)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)