from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Device


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Configuración personalizada del panel de administración para el modelo User.
    Basado exclusivamente en 'email' como identificador principal.
    """
    # Columnas visibles en la lista
    list_display = ("email", "phone_number", "is_staff", "is_active", "created_at")
    
    # Filtros laterales
    list_filter = ("is_staff", "is_superuser", "is_active", "created_at")
    
    # Campos de búsqueda
    search_fields = ("email", "phone_number")
    
    # Orden predeterminado (más recientes primero)
    ordering = ("-created_at",)

    # Estructura del formulario de edición dentro del admin
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Información Personal"), {"fields": ("phone_number",)}),
        (
            _("Permisos"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Fechas importantes"), {"fields": ("last_login", "created_at", "updated_at")}),
    )

    # Campos de solo lectura al editar un usuario
    readonly_fields = ("created_at", "updated_at", "last_login")

    # Formulario para la creación de un nuevo usuario desde el admin
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password", "phone_number"),
            },
        ),
    )


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    """
    Configuración del panel de administración para auditoría de dispositivos.
    """
    list_display = ("user", "device_name", "ip_address", "is_trusted", "last_login_at")
    list_filter = ("is_trusted", "created_at")
    search_fields = ("user__email", "device_name", "ip_address")
    ordering = ("-last_login_at",)
    