# 🏦 WalletHub API

API RESTful backend construida con **Django REST Framework (DRF)** y **PostgreSQL** para la gestión de billeteras digitales, transacciones financieras y autenticación segura con JWT.

---

## 🚀 Tecnologías Principales

* **Lenguaje:** Python 3.11+
* **Framework:** Django 5.2.17 & Django REST Framework
* **Autenticación:** JWT (SimpleJWT) headless basado en Email
* **Base de Datos:** PostgreSQL
* **Contenedores:** Docker & Docker Compose

---

## 🛠️ Arquitectura del Proyecto

El proyecto sigue un patrón modular estructurado dentro del directorio `apps/`:

```text
wallethub_api/
├── apps/
│   ├── authentication/   # Modelo User personalizado, Auth JWT y audit de dispositivos
│   ├── wallet/           # Gestión de saldos, cuentas y límites
│   └── transactions/     # Histórico de transferencias, depósitos y cobros
├── config/               # Configuración global de Django (settings, urls, wsgi)
├── docker-compose.yml    # Servicios locales (PostgreSQL)
├── manage.py
├── requirements.txt
└── .env.example
