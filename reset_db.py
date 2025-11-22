# reset_db.py
from persistence.db import engine, Base
# IMPORTANTE: Importar los modelos para que SQLAlchemy sepa qué crear
import entities.models

print("1. Borrando tablas viejas...")
Base.metadata.drop_all(bind=engine)

print("2. Creando tablas nuevas con la columna password...")
Base.metadata.create_all(bind=engine)

print("¡Listo! Base de datos actualizada.")