from django.contrib.auth import get_user_model
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from .serializers import GetUserWalletIdSerializer, UserProfileSerializer, UserRegisterSerializer, LogoutSerializer, ChangePasswordSerializer, DeviceSerializer
from .models import Device

User = get_user_model()

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # Ignora la busqueda por ID en la BD y retoma la instancia actual del JWT
        return self.request.user
    
class UserRegisterView(generics.CreateAPIView):
    serializer_class = UserRegisterSerializer
    permission_classes = [AllowAny]

class LogoutView(generics.GenericAPIView):
    serializer_class = LogoutSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Sesión cerrada correctamente."},
            status=status.HTTP_200_OK,
        )

class UserSearchView(generics.GenericAPIView):
    serializer_class = GetUserWalletIdSerializer
    permission_classes=[IsAuthenticated]

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
            # busca por email sin importar si esat en mayuscula o minuscula
            target_user = User.objects.select_related("wallet").get(email__iexact=email)
        except  User.DoesNotExist:
            return Response(
                {"detail": "No se encontro usario registrado con ese correo"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serilizer = self.get_serializer(target_user)
        return Response(serilizer.data, status=status.HTTP_200_OK)

class ChangePasswordView(generics.GenericAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Contraseña actualizada exitosamente."},
            status=status.HTTP_200_OK,
        )

class DeviceListCreateView(generics.ListCreateAPIView):
    serializer_class = DeviceSerializer
    permission_classes = [IsAuthenticated]

    # unica responsabilidad de la vista: restringir el acceso a la BD
    def get_queryset(self):
        return Device.objects.filter(user=self.request.user)


class DeviceRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = DeviceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # DRF busca el <uuid> de la URL automaticamente DENTRO de esta lista filtrada
        return Device.objects.filter(user=self.request.user)