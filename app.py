from flask import Flask, request, jsonify
from persistence.db import engine, Base, SessionLocal
# Importamos tus modelos
from entities.models import User, Category, Thread, Comment

app = Flask(__name__)

# CREAR TABLAS (Solo si no existen)
Base.metadata.create_all(bind=engine)


# --- UTILIDAD PARA LA DB ---
def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        # No cerramos aquí para poder usarla en la función,
        # pero idealmente se maneja con dependencias.
        # Para este ejemplo simple, cerraremos manual en la ruta.
        pass


# --- RUTA 1: CREAR CATEGORÍA (POST) ---
# Necesitamos esto primero: "Memes", "Informática", etc.
@app.route('/categories', methods=['POST'])
def create_category():
    data = request.get_json()  # Recibe el JSON del cliente

    # Validamos que envíen el nombre
    if not 'name' in data:
        return jsonify({"error": "El nombre es obligatorio"}), 400

    db = SessionLocal()
    try:
        # Creamos la entidad
        new_cat = Category(name=data['name'])
        db.add(new_cat)
        db.commit()
        db.refresh(new_cat)  # Recargamos para obtener el ID generado
        return jsonify({"id": new_cat.id, "name": new_cat.name, "message": "Categoría creada!"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


# --- RUTA 2: CREAR USUARIO (POST) ---
@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()

    db = SessionLocal()
    try:
        new_user = User(username=data['username'], email=data['email'])
        db.add(new_user)
        db.commit()
        return jsonify({"message": f"Usuario {new_user.username} creado con éxito!"}), 201
    except Exception as e:
        return jsonify({"error": "Error creando usuario (quizás el email ya existe)"}), 400
    finally:
        db.close()


# --- RUTA 3: VER TODOS LOS USUARIOS (GET) ---
@app.route('/users', methods=['GET'])
def get_users():
    db = SessionLocal()
    users = db.query(User).all()
    db.close()

    # Convertimos la lista de objetos a JSON
    result = [{"id": u.id, "username": u.username} for u in users]
    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True)