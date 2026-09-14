from django.http import JsonResponse

def custom_404_handler(request, exception=None):
    return JsonResponse(
        {
            "detail": "La ruta solicitada no fue encontrada.",
            "code": "not_found",
            "status": 404
        },
        status=404
    )

def custom_500_handler(request):
    return JsonResponse(
        {
            "detail": "Error interno del servidor.",
            "code": "server_error",
            "status": 500
        },
        status=500
    )