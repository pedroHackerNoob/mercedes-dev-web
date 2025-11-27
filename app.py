from flask import Flask, request, jsonify, render_template
from flask import flash, redirect, url_for, render_template, request # Asegúrate de tener estos imports
from persistence.db import engine, Base, SessionLocal
# Importamos tus modelos
from entities.models import User, Category, Thread, Comment
# Herramientas de seguridad
from werkzeug.security import generate_password_hash, check_password_hash
# FLASK-LOGIN
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
app = Flask(__name__)

# SECRET_KEY (Para firmar las cookies)
app.config['SECRET_KEY'] = 'una_palabra_secreta_muy_dificil'

#INICIALIZAR EL LOGIN MANAGER
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # A dónde redirigir si no está logueado

# CREAR TABLAS (Solo si no existen)
# Base.metadata.create_all(bind=engine)

# 4. EL "USER LOADER" (Vital: Le dice a Flask cómo buscar al usuario por su ID en la cookie)
@login_manager.user_loader
def load_user(user_id):
    db = SessionLocal()
    try:
        # Buscamos el usuario en la DB usando el ID que viene en la cookie
        return db.query(User).get(int(user_id))
    finally:
        db.close()

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
def landingPage():
    return render_template('landingPage.html')


@app.route('/signup')
def signupPage():
    return render_template('signUp.html')


# --- RUTA: CREAR CATEGORÍA (POST) ---
@app.route('/api/categories', methods=['POST'])
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


# --- RUTA: CREAR USUARIO (POST) ---
@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.get_json()

    # Validamos que venga el password
    if not 'password' in data:
        return jsonify({"error": "La contraseña es obligatoria"}), 400

    db = SessionLocal()
    try:
        # ENCRIPTAMOS LA CONTRASEÑA ANTES DE GUARDAR
        hashed_password = generate_password_hash(data['password'])

        new_user = User(
            username=data['username'],
            email=data['email'],
            password=hashed_password  # Guardamos el garabato seguro, no el texto plano
        )

        db.add(new_user)
        db.commit()
        return jsonify({"message": f"Usuario {new_user.username} creado con seguridad!"}), 201
    except Exception as e:
        return jsonify({"error": f"Error creando usuario: {str(e)}"}), 400
    finally:
        db.close()


# --- RUTA: VER TODOS LOS USUARIOS (GET) ---
@app.route('/api/users', methods=['GET'])
def get_users():
    db = SessionLocal()
    users = db.query(User).all()
    db.close()

    # Convertimos la lista de objetos a JSON
    result = [{"id": u.id, "username": u.username} for u in users]
    return jsonify(result)


# --- RUTA: PUBLICAR UN HILO (THREAD) ---
@app.route('/api/threads', methods=['POST'])
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


# --- RUTA: COMENTAR UN HILO ---
@app.route('/api/comments', methods=['POST'])
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


# --- RUTA: VER HILOS CON SUS COMENTARIOS (EL FEED) ---
@app.route('/api/feed', methods=['GET'])
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


# --- VER UN HILO ESPECÍFICO (GET) ---
@app.route('/api/threads/<int:thread_id>', methods=['GET'])
def get_single_thread(thread_id):
    db = SessionLocal()
    try:
        thread = db.query(Thread).filter(Thread.id == thread_id).first()
        if not thread:
            return jsonify({"error": "Hilo no encontrado"}), 404

        # Retornamos el hilo con sus detalles
        return jsonify({
            "id": thread.id,
            "title": thread.title,
            "content": thread.content,
            "author": thread.author.username,
            "category": thread.category.name
        })
    finally:
        db.close()


# --- BORRAR UN HILO (DELETE) ---
@app.route('/api/threads/<int:thread_id>', methods=['DELETE'])
def delete_thread(thread_id):
    db = SessionLocal()
    try:
        thread = db.query(Thread).filter(Thread.id == thread_id).first()
        if not thread:
            return jsonify({"error": "Hilo no encontrado"}), 404

        # OJO: Al borrar el hilo, se borrarán los comentarios si configuramos CASCADE
        # Si no, primero deberíamos borrar los comentarios manualmente.
        # Intentemos borrar directo:
        db.delete(thread)
        db.commit()
        return jsonify({"message": "Hilo eliminado correctamente"}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": f"No se pudo borrar: {str(e)}"}), 500
    finally:
        db.close()


# --- BORRAR COMENTARIO (DELETE) ---
@app.route('/api/comments/<int:comment_id>', methods=['DELETE'])
def delete_comment(comment_id):
    db = SessionLocal()
    try:
        comment = db.query(Comment).filter(Comment.id == comment_id).first()
        if not comment:
            return jsonify({"error": "Comentario no encontrado"}), 404

        db.delete(comment)
        db.commit()
        return jsonify({"message": "Comentario eliminado"}), 200
    finally:
        db.close()


# --- ACTUALIZAR USUARIO (PUT) ---
@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json()
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({"error": "Usuario no encontrado"}), 404

        # Actualizamos solo lo que envíen
        if 'username' in data:
            user.username = data['username']
        if 'email' in data:
            user.email = data['email']

        db.commit()
        return jsonify({"message": "Usuario actualizado"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        db.close()


# --- BORRAR USUARIO (DELETE) ---
@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({"error": "Usuario no encontrado"}), 404

        db.delete(user)
        db.commit()
        return jsonify({"message": "Usuario eliminado. Adiós vaquero."}), 200
    except Exception as e:
        # Seguramente fallará si el usuario tiene posts (por integridad de la DB)
        return jsonify({"error": "No se puede borrar el usuario porque tiene hilos o comentarios activos."}), 400
    finally:
        db.close()


# --- VER TODAS LAS CATEGORÍAS (GET) ---
@app.route('/api/categories', methods=['GET'])
def get_categories():
    db = SessionLocal()
    cats = db.query(Category).all()
    db.close()
    return jsonify([{"id": c.id, "name": c.name} for c in cats])

@app.route('/api/login')
def loginPage():
    return render_template('logIn.html')

# --- RUTA LOGIN (Verificar contraseña) ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    # 1. SI ENTRAN POR GET: Solo mostramos el formulario
    if request.method == 'GET':
        # Si ya está logueado, lo mandamos directo al perfil
        if current_user.is_authenticated:
            return redirect(url_for('profile'))
        return render_template('login.html')

    # 2. SI ENTRAN POR POST: Procesamos los datos

    # Truco para soportar tanto Postman (JSON) como Navegador (Form)
    if request.is_json:
        data = request.get_json()
        username = data.get('inputUserName')
        password = data.get('inputPassword')
    else:
        # Aquí capturamos los datos del <input name="username">
        username = request.form.get('inputUserName')
        password = request.form.get('inputPassword')

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)

            # Si es navegador, redirigimos a la página visual
            if not request.is_json:
                return redirect(url_for('profile'))

            # Si es Postman, devolvemos JSON
            return jsonify({"message": "Login Exitoso"}), 200
        else:
            # Si falló
            if not request.is_json:
                flash("Usuario o contraseña incorrectos")  # Mensaje para el HTML
                return redirect(url_for('login'))  # Recargamos el login

            return jsonify({"error": "Credenciales inválidas"}), 401
    finally:
        db.close()


# LOGOUT
@app.route('/api/logout')
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Sesión cerrada"}), 200

@app.route('/profile')
@login_required # <--- Esto protege la ruta. Si no estás logueado, te patea.
def profile():
    # No necesitamos consultar la DB, current_user ya tiene los datos
    return render_template('profileUser.html', user=current_user)

if __name__ == '__main__':
    app.run(debug=True)