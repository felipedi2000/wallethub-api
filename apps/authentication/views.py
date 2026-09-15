from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib.auth import get_user_model

from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .models import Device
from django.contrib.auth import get_user_model
from .serializers import GetUserWalletIdSerializer, UserProfileSerializer, UserRegisterSerializer, LogoutSerializer, ChangePasswordSerializer, DeviceSerializer
from apps.shared.throttles import (
    CustomAnonRateThrottle,
    UserSearchRateThrottle,
    StrictAnonRateThrottle,
    CustomUserRateThrottle
)


User = get_user_model()


# solo para documentacion
@extend_schema(
    tags=["Authentication"],
    summary="Obtener tokens JWT",
    description="Inicia sesión con email y contraseña. Devuelve los tokens de acceso y refresco."
)
class CustomTokenObtainPairView(TokenObtainPairView):
    """Login del usuario"""
    pass


@extend_schema(
    tags=["Authentication"],
    summary="Refrescar token de acceso",
    description="Genera un nuevo token de acceso (Access Token) válido enviando un token de refresco (Refresh Token) no expirado."
)
class CustomTokenRefreshView(TokenRefreshView):
    """Refrescar token JWT"""
    pass


@extend_schema(
    tags=["Authentication"],
    summary="Obtener o actualizar perfil de usuario",
    description="Permite consultar y actualizar los datos del perfil del usuario actualmente autenticado."
)
class UserProfileView(generics.RetrieveUpdateAPIView):
    """Obtener y actualizar perfil del usuario autenticado"""
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [CustomUserRateThrottle]

    def get_object(self):
        return self.request.user


@extend_schema(
    tags=["Authentication"],
    summary="Registrar nuevo usuario",
    description=(
        "Crea una nueva cuenta de usuario en la plataforma y desencadena la inicialización automática de su cuenta financiera.\n\n"
        "### Arquitectura de Eventos (Django Signals):\n"
        "* **`post_save` Signal (User -> Wallet):** Tras la creación exitosa del usuario, una señal genera de forma automática su billetera inicial con saldo `0.00` y moneda por defecto.\n"
        "* **`post_save` Signal (User -> TransactionLimits):** Se asignan automáticamente los límites transaccionales por defecto (diario y mensual) vinculados al perfil del usuario."
    ),
)
class UserRegisterView(generics.CreateAPIView):
    """Registrar nuevo usuario en la plataforma"""
    serializer_class = UserRegisterSerializer
    permission_classes = [AllowAny]


@extend_schema(
    tags=["Authentication"],
    summary="Cerrar sesión",
    description="Invalida el token de refresco actual enviándolo a la lista negra (blacklist).",
)
class LogoutView(generics.GenericAPIView):
    """Cerrar sesión del usuario"""
    serializer_class = LogoutSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [StrictAnonRateThrottle]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Sesión cerrada correctamente."},
            status=status.HTTP_200_OK,
        )


@extend_schema(
    tags=["Authentication"],
    summary="Buscar usuario por email",
    description="Busca la billetera de un destinatario mediante su correo electrónico para realizar transferencias de dinero.",
    parameters=[
        OpenApiParameter(
            name="email",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            required=True,
            description="Correo electrónico del usuario a buscar (búsqueda insensible a mayúsculas)."
        )
    ],
)
class UserSearchView(generics.GenericAPIView):
    """Buscar usuario por email para transferencias"""
    serializer_class = GetUserWalletIdSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserSearchRateThrottle]

    def get(self, request, *args, **kwargs):
        email = request.query_params.get("email")

        if not email:
            return Response(
                {"detail": "El parámetro 'email' es requerido."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if email.lower() == request.user.email.lower():
            return Response(
                {"detail": "No puedes buscar tu propia cuenta para realizar transferencias."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            target_user = User.objects.select_related("wallet").get(email__iexact=email)
        except User.DoesNotExist:
            return Response(
                {"detail": "No se encontro usario registrado con ese correo"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.get_serializer(target_user)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Authentication"],
    summary="Cambiar contraseña",
    description="Permite actualizar la contraseña del usuario validando la clave actual.",
)
class ChangePasswordView(generics.GenericAPIView):
    """Cambiar contraseña del usuario"""
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [CustomUserRateThrottle]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Contraseña actualizada exitosamente."},
            status=status.HTTP_200_OK,
        )


@extend_schema(
    tags=["Authentication"],
    summary="Listar y registrar dispositivos",
    description="Obtiene la lista de dispositivos autorizados vinculados a la cuenta o registra uno nuevo."
)
class DeviceListCreateView(generics.ListCreateAPIView):
    """Listar y crear dispositivos del usuario"""
    serializer_class = DeviceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Device.objects.filter(user=self.request.user)


@extend_schema(
    tags=["Authentication"],
    summary="Gestión individual de dispositivo",
    description="Permite obtener detalles, actualizar información o desvincular un dispositivo específico mediante su ID."
)
class DeviceRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """Obtener, actualizar y eliminar dispositivo"""
    serializer_class = DeviceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Device.objects.filter(user=self.request.user)