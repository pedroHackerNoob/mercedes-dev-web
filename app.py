from flask import Flask, request, jsonify, render_template
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
# ---Ruta 0: test (GET) ---
@app.route('/')
def hello_world():
    return render_template('index.html')

# --- RUTA 1: CREAR CATEGORÍA (POST) ---
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


# --- RUTA 4: PUBLICAR UN HILO (THREAD) ---
@app.route('/threads', methods=['POST'])
def create_thread():
    data = request.get_json()
    # Validamos datos mínimos
    if not all(k in data for k in ("title", "content", "user_id", "category_id")):
        return jsonify({"error": "Faltan datos (title, content, user_id, category_id)"}), 400

    db = SessionLocal()
    try:
        # Creamos el hilo
        new_thread = Thread(
            title=data['title'],
            content=data['content'],
            user_id=data['user_id'],
            category_id=data['category_id']
        )
        db.add(new_thread)
        db.commit()
        return jsonify({"message": "Hilo publicado con éxito!"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        db.close()


# --- RUTA 5: COMENTAR UN HILO ---
@app.route('/comments', methods=['POST'])
def create_comment():
    data = request.get_json()
    if not all(k in data for k in ("content", "user_id", "thread_id")):
        return jsonify({"error": "Faltan datos (content, user_id, thread_id)"}), 400

    db = SessionLocal()
    try:
        new_comment = Comment(
            content=data['content'],
            user_id=data['user_id'],
            thread_id=data['thread_id']
        )
        db.add(new_comment)
        db.commit()
        return jsonify({"message": "Comentario agregado!"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        db.close()


# --- RUTA 6: VER HILOS CON SUS COMENTARIOS (EL FEED) ---
@app.route('/feed', methods=['GET'])
def get_feed():
    db = SessionLocal()
    # Traemos todos los hilos
    threads = db.query(Thread).all()

    # Armamos un JSON complejo (Hilo + Autor + Categoría + Comentarios)
    results = []
    for t in threads:
        results.append({
            "id": t.id,
            "title": t.title,
            "content": t.content,
            "author": t.author.username,
            "category": t.category.name,
            "comments": [{"author": c.author.username, "content": c.content} for c in t.comments]
        })
    db.close()
    return jsonify(results)
if __name__ == '__main__':
    app.run(debug=True)