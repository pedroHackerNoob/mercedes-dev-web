from flask import Flask, request, jsonify, render_template
from flask import flash, redirect, url_for, render_template, request # Asegúrate de tener estos imports
from persistence.db import engine, Base, SessionLocal
# Importamos tus modelos
from entities.models import User, Category, Thread, Comment
# Herramientas de seguridad
from werkzeug.security import generate_password_hash, check_password_hash
# FLASK-LOGIN
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from sqlalchemy import desc  # Importar para ordenar descendente
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


@app.route('/')
def landing_page():
    # Si estás logueado y vas aquí, mejor te mando a tu perfil
    if current_user.is_authenticated:
        return redirect(url_for('profile'))

    # Si no, muestro la bienvenida
    return render_template('landingPage.html')


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


# ==========================================
# 🤖 API SIGN UP (Para Postman)
# ==========================================
@app.route('/api/signup', methods=['POST'])
def api_signup():
    data = request.get_json()
    # Validamos que lleguen los datos
    if not data or not all(k in data for k in ("username", "email", "password")):
        return jsonify({"error": "Faltan datos (username, email, password)"}), 400

    db = SessionLocal()
    try:
        # 1. Verificar si ya existe
        existing_user = db.query(User).filter(
            (User.username == data['username']) | (User.email == data['email'])
        ).first()

        if existing_user:
            return jsonify({"error": "El usuario o email ya existen"}), 400

        # 2. Encriptar contraseña
        hashed_pw = generate_password_hash(data['password'])

        # 3. Crear usuario
        new_user = User(
            username=data['username'],
            email=data['email'],
            password=hashed_pw
        )
        db.add(new_user)
        db.commit()

        return jsonify({"message": "Usuario registrado con éxito"}), 201
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


# ==========================================
# 🌐 WEB SIGN UP (Para Navegador)
# ==========================================
@app.route('/signup', methods=['GET', 'POST'])
def web_signup():
    if request.method == 'GET':
        if current_user.is_authenticated:
            return redirect(url_for('profile'))
        return render_template('signUp.html')

    username = request.form.get('inputUserName')
    email = request.form.get('inputEmail')
    password = request.form.get('inputPassword')
    print(username, email, password)
    db = SessionLocal()
    try:
        # 1. Validar duplicados
        existing_user = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing_user:
            flash("Error: El nombre de usuario o correo ya están en uso.")
            return redirect(url_for('web_signup'))  # Recargamos el formulario

        # 2. Crear y Guardar
        hashed_pw = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_pw)

        db.add(new_user)
        db.commit()

        # 3. Éxito -> Mandar al Login
        flash("¡Cuenta creada! Por favor inicia sesión.")
        return redirect(url_for('web_login'))

    except Exception as e:
        db.rollback()
        flash(f"Ocurrió un error: {str(e)}")
        return redirect(url_for('web_signup'))
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


# ==========================================
# 🤖 ZONA API (Para Postman, React, Móvil)
# Devuelve solo JSON
# ==========================================
@app.route('/api/login', methods=['POST'])
def api_login():
    # Solo aceptamos JSON
    data = request.get_json()
    if not data:
        return jsonify({"error": "Se requiere JSON"}), 400

    username = data.get('username')
    password = data.get('password')

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)  # Crea la sesión (cookie)
            return jsonify({
                "message": "Login API exitoso",
                "user_id": user.id,
                "username": user.username
            }), 200
        else:
            return jsonify({"error": "Credenciales inválidas"}), 401
    finally:
        db.close()


@app.route('/api/logout', methods=['POST'])
@login_required
def api_logout():
    logout_user()
    return jsonify({"message": "Sesión cerrada (API)"}), 200

# ==========================================
# 🌐 ZONA WEB (Para Navegadores)
# Devuelve HTML y Redirecciones
# ==========================================
@app.route('/login', methods=['GET', 'POST'])
def web_login():
    # 1. GET: Mostrar el formulario
    if request.method == 'GET':
        if current_user.is_authenticated:
            return redirect(url_for('profile'))
        return render_template('logIn.html')

    # 2. POST: Procesar el formulario HTML
    username = request.form.get('inputUserName')
    password = request.form.get('inputPassword')

    print(username, password)

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            # En web, redirigimos al perfil visual
            return redirect(url_for('profile'))
        else:
            flash("Usuario o contraseña incorrectos")
            # return redirect(url_for('web_login'))  # Recargamos la misma ruta
            return redirect(url_for('landing_page'))
    finally:
        db.close()


@app.route('/logout')
@login_required
def web_logout():
    logout_user()
    # En web, redirigimos a la página de inicio
    return redirect(url_for('landing_page'))


@app.route('/profile')
@login_required # <--- Esto protege la ruta. Si no estás logueado, te patea.
def profile():
    # No necesitamos consultar la DB, current_user ya tiene los datos
    return render_template('profileUser.html', user=current_user)


# --- RUTA 1: EL FEED VISUAL (GET) ---
@app.route('/')
@app.route('/feed')
@login_required
def web_feed():
    db = SessionLocal()
    try:
        # Traemos los hilos ordenados por fecha de creación (el más nuevo primero)
        # SQLAlchemy hace la magia de traer los comentarios automáticamente cuando los pidamos en el HTML
        threads = db.query(Thread).order_by(desc(Thread.created_at)).all()
        return render_template('feed.html', threads=threads)
    finally:
        db.close()
# --- RUTA 2: CREAR COMENTARIO DESDE LA WEB (POST) ---
@app.route('/create_comment_web', methods=['POST'])
@login_required
def create_comment_web():
    thread_id = request.form.get('thread_id')  # Viene del input oculto
    content = request.form.get('content')

    if not content or not thread_id:
        flash("El comentario no puede estar vacío")
        return redirect(url_for('web_feed'))

    db = SessionLocal()
    try:
        new_comment = Comment(
            content=content,
            user_id=current_user.id,
            thread_id=thread_id
        )
        db.add(new_comment)
        db.commit()
        flash("Comentario agregado!")
    except Exception as e:
        flash(f"Error al comentar: {str(e)}")
    finally:
        db.close()

    # Recargamos el feed para ver el nuevo comentario
    return redirect(url_for('web_feed'))
if __name__ == '__main__':
    app.run(debug=True)