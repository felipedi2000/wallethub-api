from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema,extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from apps.authentication.models import Device
from apps.transactions.paginations import StandardResultsSetPagination
from apps.shared.throttles import TransactionThrottle, CustomUserRateThrottle
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

@extend_schema_view(
    list=extend_schema(
        summary="Listar transacciones activas",
        description="Obtiene un listado de todas las transacciones asociadas a la billetera del usuario autenticado."
    ),
    retrieve=extend_schema(
        summary="Obtener detalle de transacción",
        description="Devuelve el detalle completo de una transacción específica por su ID."
    ),
)
@extend_schema(tags=["Transactions"])
class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """Gestionar transacciones y transferencias"""
    def get_throttles(self):
        action_name = getattr(self, "action", None)
        if action_name in ["transfer", "deposit"]:
            return [TransactionThrottle()]

        return [CustomUserRateThrottle()]

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

    @extend_schema(
        tags=["Transactions"],
        summary="Transferir dinero entre billeteras",
        description=(
            "Ejecuta una transferencia de fondos atómica entre la billetera del usuario autenticado y un destinatario.\n\n"
            "### Garantías de Arquitectura:\n"
            "* **Transaccionalidad Atómica (`atomic`):** Garantiza que el débito y el crédito se completen en su totalidad o se reviertan totalmente (Rollback) ante cualquier fallo.\n"
            "* **Control de Concurrencia (`select_for_update`):** Bloquea los registros de las billeteras involucradas en un orden estricto para evitar condiciones de carrera (*Race Conditions*) y prevenimos *Deadlocks*.\n"
            "* **Idempotencia (`X-Idempotency-Key`):** Encabezado obligatorio (UUIDv4). Peticiones duplicadas con la misma clave devolverán la respuesta en caché sin procesar un doble débito."
        ),
        parameters=[
            OpenApiParameter(
                name="X-Idempotency-Key",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
                required=True,
                description="Clave única (UUIDv4) para asegurar la idempotencia de la transferencia.",
            ),
        ],

    )
    @action(detail=False, methods=["post"], url_path="transfer")
    @idempotency_key_required
    def transfer(self, request):
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

    @extend_schema(
        tags=["Transactions"],
        summary="Depositar dinero a la billetera",
        description=(
            "Acredita un monto de dinero a la billetera del usuario autenticado de forma atómica.\n\n"
            "### Garantías Técnicas:\n"
            "* **Consistencia de Datos:** Incrementa el saldo dentro de una transacción acotada para reflejar el estado en tiempo real sin inconsistencias.\n"
            "* **Garantía de Idempotencia:** Requiere el encabezado `X-Idempotency-Key` (UUIDv4) para asegurar que fallos de conexión no generen recargas dobles."
        ),
        parameters=[
            OpenApiParameter(
                name="X-Idempotency-Key",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
                required=True,
                description="Clave única (UUIDv4) para asegurar la idempotencia del depósito.",
            ),
        ],
    )
    @action(detail=False, methods=["post"], url_path="deposit")
    @idempotency_key_required
    def deposit(self, request):
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

@extend_schema(
    tags=["Transactions"],
    summary="Consultar límites de transacción",
    description="Devuelve los límites diarios y mensuales asignados al usuario autenticado, junto con sus montos acumulados y disponibles.",
)
class UserLimitsMeAPIView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [CustomUserRateThrottle]

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

@extend_schema_view(
    list=extend_schema(
        tags=["Transactions"],
        summary="Consultar historial paginado de transacciones",
        description="Obtiene una lista cronológica paginada de todas las transferencias e ingresos vinculados al usuario autenticado."
    ),
    retrieve=extend_schema(
        tags=["Transactions"],
        summary="Obtener detalle histórico de una transacción",
        description="Muestra los datos detallados de un registro histórico en particular mediante su ID."
    ),
)
class TransactionHistoryView(viewsets.ReadOnlyModelViewSet):
    """Historial de transacciones del usuario"""
    serializer_class = TransactionListSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [CustomUserRateThrottle]
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