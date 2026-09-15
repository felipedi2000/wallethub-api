# 💳 WalletHub API — FinTech Backend Core

**Entorno de Producción / Swagger UI:** [https://wallethub-api.onrender.com/api/docs/](https://wallethub-api.onrender.com/api/redoc/)

API RESTful de grado empresarial para la gestión de billeteras digitales, procesamiento de transferencias atómicas, depósitos y auditoría de seguridad. Construida sobre Django REST Framework con garantías de consistencia contable, idempotencia y control de concurrencia.

---

## 🛠️ Stack Tecnológico & Arquitectura

* **Framework:** Python / Django REST Framework
* **Documentación & OpenAPI:** `drf-spectacular` (Swagger UI / ReDoc)
* **Seguridad:** JWT (SimpleJWT) con invalidación por lista negra (*Blacklist*), vinculación de dispositivos y Rate Limiting multicapa.
* **Infraestructura:** Docker / Docker Compose
* **Base de Datos & ORM:** PostgreSQL (optimizado con `select_for_update`, `select_related` y transacciones atómicas `atomic()`)

---

## 📁 Estructura del Proyecto

```text
wallethub_api/
├── apps/
│   ├── authentication/   # Gestión de usuarios, autenticación JWT, managers y dispositivos
│   ├── shared/           # Módulos compartidos y throttles de seguridad
│   ├── transactions/     # Procesamiento de transferencias atómicas, depósitos e historial
│   └── wallet/           # Billeteras digitales, límites de monto y señales desacopladas
├── config/               # Configuración global del proyecto
└── tests/                # Suite completa de pruebas unitarias e integración
