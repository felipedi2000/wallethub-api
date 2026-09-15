from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url
import os
import sys

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

sys.path.insert(0, str(BASE_DIR))

SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-fallback-key-replace-in-env")
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("ALLOWED_HOSTS", "127.0.0.1,localhost,.koyeb.app,.onrender.com").split(",")
    if host.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",

    "apps.authentication",
    "apps.wallet",
    "apps.transactions",

    "drf_spectacular",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            ssl_require=True if not DEBUG else False,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("POSTGRES_DB"),
            "USER": os.getenv("POSTGRES_USER"),
            "PASSWORD": os.getenv("POSTGRES_PASSWORD"),
            "HOST": os.getenv("POSTGRES_HOST", "localhost"),
            "PORT": os.getenv("POSTGRES_PORT", "5432"),
            "CONN_MAX_AGE": 60,
        }
    }

AUTH_USER_MODEL = "authentication.User"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "es-co"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True


STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

ENABLE_ADMIN = os.getenv("ENABLE_ADMIN", "False").lower() in ("true", "1", "t")

CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]

# Configuración SSL en Producción
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=int(os.getenv("JWT_ACCESS_TOKEN_LIFETIME_MINUTES", 15))
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=int(os.getenv("JWT_REFRESH_TOKEN_LIFETIME_DAYS", 1))
    ),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_THROTTLE_CLASSES": [
        "apps.shared.throttles.CustomAnonRateThrottle",
        "apps.shared.throttles.CustomUserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "20/minute",     
        "user": "100/minute",
        "user_search": "30/minute",
        "auth_strict": "5/minute", 
        "transactions": "10/minute",
    },
     "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
    ),

    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}


SPECTACULAR_SETTINGS = {
    "TITLE": "Wallet Hub API",
    "DESCRIPTION": "API para gestionar billeteras y transacciones digitales",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "CONTACT": {
        "name": "Soporte Wallet Hub",
        "email": "felipe.edi2000@gmail.com",
        "url": "https://github.com/felipedi2000/wallethub-api/"
    },
    "LICENSE": {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    },
    "TAGS": [
        {
            "name": "Authentication",
            "description": (
                "Autenticación, registro y gestión de usuarios.\n\n"
                "* **Control de Tráfico (Rate Limiting):** Protección estricta contra ataques de fuerza bruta en inicio/cierre de sesión y registro.\n"
                "* **Prevención de Enumeración:** Límite de tasa especializado en la búsqueda de correos para evitar el raspado (*scraping*) de usuarios.\n"
                "* **Inicialización Automática:** La creación de una cuenta desencadena la instanciación automática de su billetera y sus límites transaccionales."
            ),
        },
        {
            "name": "Wallet",
            "description": "Gestión de billeteras y saldos con límite general de tasa de peticiones por usuario.",
        },
        {
            "name": "Transactions",
            "description": (
                "Gestión de transacciones, transferencias atómicas y depósitos.\n\n"
                "* **Rate Limiting:** Operaciones críticas restringidas mediante `TransactionThrottle` "
                "para mitigar ráfagas no autorizadas y prevenir saturación en la base de datos.\n"
                "* **Idempotencia:** Endpoints de escritura exigen `X-Idempotency-Key` para prevenir peticiones duplicadas.\n"
                "* **Concurrencia:** Bloqueos pesimistas (`select_for_update`) a nivel de base de datos para garantizar consistencia del saldo."
            ),
        },
    ],
    "SORT_OPERATIONS_BY_METHODS": False,
    "ENABLE_DJANGO_DECORATORS": True,
    "SORT_OPERATIONS": False,
    "SORT_OPERATION_PARAMETERS": False,
}