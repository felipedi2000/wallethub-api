from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .decorators import idempotency_key_required
from .models import Transaction
from .serializers import (
    DepositCreateSerializer,
    TransactionDetailSerializer,
    TransferCreateSerializer,
    UserTransactionLimitSerializer
)
from .services import TransactionService


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    permissions_classes = [IsAuthenticated]

    def get_queryset(self):

        user_wallet = self.request.user.wallet

        return (
            (
                Transaction.objects.filter(wallet_from=user_wallet)
                | Transaction.objects.filter(wallet_to=user_wallet)
            )
            .distinct()
            .select_related("wallet_from", "wallet_to")
            .prefetch_related("movements")
        )

    # serializer clase se define ya que no se pasa
    def get_serializer_class(self):
        if self.action == "transfer":
            return TransferCreateSerializer
        if self.action == "deposit":
            return DepositCreateSerializer
        return TransactionDetailSerializer

    # se agregan meotods post para transferencias a los meotods base de viwe set
    @action(detail=False, methods=["post"], url_path="transfer")
    @idempotency_key_required
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
                amount=serializer.validated_data["amount"],
                description=serializer.validated_data.get("description", ""),
            )
        except DjangoValidationError as e:
            raise DRFValidationError(e.messages)

        response_serializer = TransactionDetailSerializer(transaction_obj)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], url_path="deposit")
    @idempotency_key_required
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
                description=serializer.validated_data.get("description", ""),
            )
        except DjangoValidationError as e:
            raise DRFValidationError(e.messages)

        response_serializer = TransactionDetailSerializer(transaction_obj)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class UserLimitsMeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        limits = getattr(user, "transaction_limit", None)

        if not limits:
            return Response(
                {
                    "daily_limit": "0.00",
                    "daily_spent": "0.00",
                    "daily_available": "0.00",
                    "monthly_limit": "0.00",
                    "monthly_spent": "0.00",
                    "monthly_available": "0.00",
                },
                status=status.HTTP_200_OK
            )
        serializer = UserTransactionLimitSerializer(limits)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )
