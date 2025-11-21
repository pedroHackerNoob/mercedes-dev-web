import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 1. Obtenemos la URL de Render o usamos una local por defecto
# DATABASE_URL es la variable que Render crea automáticamente
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://rayan:W1fjeCrTQiV575iW8P6BRbAV9vl1vJcw@dpg-d4gddi9r0fns738c9ms0-a.oregon-postgres.render.com/reach_ehnv")

# 2. Parche para Render (Postgres requiere 'postgresql://', pero Render a veces da 'postgres://')
if SQLALCHEMY_DATABASE_URL and SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

# 3. Crear el engine con PostgreSQL
engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True)

# 4. Crear la sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 5. La base para los modelos
Base = declarative_base()

# Función de utilidad para obtener la sesión en tus rutas de Flask después
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()