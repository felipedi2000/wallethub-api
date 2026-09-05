import json
from functools import wraps
from rest_framework.response import Response
from rest_framework import status
from rest_framework.renderers import JSONRenderer
from .models import IdempotencyKey


def idempotency_key_required(view_func):
    @wraps(view_func)
    def _wrapped_view(view_instance, request, *args, **kwargs):
        key_header = request.headers.get("X-Idempotency-Key")

        if not key_header:
            return Response(
                {"detail": "La cabecera 'X-Idempotency-Key' es requerida para esta operación."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        idempotency_record, created = IdempotencyKey.objects.get_or_create(
            user=request.user,
            key=key_header
        )

        if not created:
            if idempotency_record.response_data is not None:
                return Response(
                    idempotency_record.response_data,
                    status=idempotency_record.response_code
                )
            return Response(
                {"detail": "Petición en proceso. Intente de nuevo en un momento."},
                status=status.HTTP_409_CONFLICT,
            )

        try:
            response = view_func(view_instance, request, *args, **kwargs)
            
            if status.is_success(response.status_code) or status.is_client_error(response.status_code):
                idempotency_record.response_code = response.status_code
                
                # Renderiza 
                rendered_data = JSONRenderer().render(response.data)
                idempotency_record.response_data = json.loads(rendered_data)
                
                idempotency_record.save()

            return response
        except Exception as e:
            idempotency_record.delete()
            raise e

    return _wrapped_view