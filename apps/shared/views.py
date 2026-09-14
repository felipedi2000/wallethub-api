# apps/shared/views.py
from rest_framework import status
from rest_framework.response import Response

def custom_404_handler(request, exception=None):
    return Response(
        {
            "detail": "La ruta solicitada no fue encontrada.",
            "code": "not_found",
            "status": 404
        },
        status=status.HTTP_404_NOT_FOUND
    )

def custom_500_handler(request):
    return Response(
        {
            "detail": "Error interno del servidor.",
            "code": "server_error",
            "status": 500
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )