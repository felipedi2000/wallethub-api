from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from apps.authentication.models import Device
from apps.transactions.paginations import StandardResultsSetPagination
from apps.transactions.throttles import TransactionThrottle

from .decorators import idempotency_key_required
from .models import Transaction
from .serializers import (
    DepositCreateSerializer,
    TransactionDetailSerializer,
    TransactionListSerializer,
    TransferCreateSerializer,
    UserTransactionLimitSerializer,
)
from .services import TransactionService


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_throttles(self):
        """
        Aplica TransactionThrottle (estricto) para transferencias y depósitos,
        y UserRateThrottle (general) para el resto de acciones de lectura.
        """
        action_name = getattr(self, "action", None)
        if action_name in ["transfer", "deposit"]:
            return [TransactionThrottle()]

        return [UserRateThrottle()]

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

    def get_serializer_class(self):
        if self.action == "transfer":
            return TransferCreateSerializer
        if self.action == "deposit":
            return DepositCreateSerializer
        return TransactionDetailSerializer

    def _get_request_context(self):
        """Extrae contexto de seguridad de la petición HTTP."""
        device_id = self.request.headers.get("X-Device-ID") or self.request.data.get("device_id")
        device = Device.objects.filter(id=device_id).first() if device_id else None

        ip_address = (
            self.request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip()
            or self.request.META.get("REMOTE_ADDR", "")
        )
        user_agent = self.request.META.get("HTTP_USER_AGENT", "")

        return {
            "device": device,
            "ip_address": ip_address,
            "user_agent": user_agent,
        }

    @action(detail=False, methods=["post"], url_path="transfer")
    @idempotency_key_required
    def transfer(self, request):
        """POST /api/v1/transactions/transfer/"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        context = self._get_request_context()
        try:
            transaction_obj = TransactionService.execute_transfer(
                sender_wallet=request.user.wallet,
                receiver_wallet_id=serializer.validated_data["receiver_wallet_id"],
                amount=serializer.validated_data["amount"],
                description=serializer.validated_data.get("description", ""),
                is_pre_blocked=serializer.validated_data.get("is_pre_blocked", False),
                **context,
            )
        except DjangoValidationError as e:
            raise DRFValidationError(e.messages)

        response_serializer = TransactionDetailSerializer(transaction_obj)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], url_path="deposit")
    @idempotency_key_required
    def deposit(self, request):
        """POST /api/v1/transactions/deposit/"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        context = self._get_request_context()

        try:
            transaction_obj = TransactionService.execute_deposit(
                wallet=request.user.wallet,
                amount=serializer.validated_data["amount"],
                description=serializer.validated_data.get("description", ""),
                **context,
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
                status=status.HTTP_200_OK,
            )

        serializer = UserTransactionLimitSerializer(limits)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TransactionHistoryView(viewsets.ReadOnlyModelViewSet):
    serializer_class = TransactionListSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        user = self.request.user

        return (
            Transaction.objects.filter(
                Q(wallet_from__user=user) | Q(wallet_to__user=user)
            )
            .select_related("wallet_from", "wallet_to")
            .order_by("-created_at")
        )