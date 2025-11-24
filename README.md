# 🌐 Flask Social Network API

Backend para una red social ligera basada en Hilos (Threads). Desarrollada con Python, Flask y PostgreSQL.

## 🚀 Características Principales

* **Arquitectura Modular:** Separación de responsabilidades entre Modelos (`entities`) y Conexión (`persistence`).
* **Base de Datos Relacional:** 4 entidades clave (User, Thread, Comment, Category).
* **Seguridad:** Encriptado de contraseñas (Hashing) con `Werkzeug`.
* **API RESTful:** Endpoints para operaciones CRUD completas.
* **Cloud Ready:** Configurada para desplegarse fácilmente en Render.com.

## 🛠️ Tecnologías

* **Lenguaje:** Python 3.x
* **Framework:** Flask
* **ORM:** SQLAlchemy
* **Base de Datos:** PostgreSQL
* **Drivers:** `psycopg2-binary`

## 📂 Estructura del Proyecto

```text
/
├── app.py                 # Punto de entrada y definición de Rutas (Endpoints)
├── persistence/
│   └── db.py              # Configuración del Engine y Session de la BD
└── entities/
    └── models.py          # Definición de Tablas (User, Thread, Comment, Category)
