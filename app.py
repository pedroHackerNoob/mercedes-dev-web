from flask import Flask, request, jsonify, render_template, flash, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import desc

from persistence.db import engine, Base, SessionLocal
from entities.models import User, Category, Thread, Comment

app = Flask(__name__)

# --- CONFIGURACIÓN ---
app.config['SECRET_KEY'] = 'una_palabra_secreta_muy_dificil'

# --- LOGIN MANAGER ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'web_login'  # Nombre de la función de la vista de login

# Base.metadata.create_all(bind=engine) # Descomentar si se necesitan crear tablas

@login_manager.user_loader
def load_user(user_id):
    db = SessionLocal()
    try:
        return db.query(User).get(int(user_id))
    finally:
        db.close()


# ==============================================================================
# 🌐 RUTAS WEB (Vistas HTML y Redirecciones)
# ==============================================================================

@app.route('/')
def landing_page():
    """Página de inicio. Si está logueado, redirige al perfil."""
    if current_user.is_authenticated:
        return redirect(url_for('web_feed'))
    return render_template('landingPage.html')


@app.route('/feed')
@login_required
def web_feed():
    """Muro principal de noticias."""
    db = SessionLocal()
    try:
        threads = db.query(Thread).order_by(desc(Thread.created_at)).all()
        return render_template('feed.html', threads=threads)
    finally:
        db.close()


@app.route('/profile')
@login_required
def profile():
    return render_template('profileUser.html', user=current_user)


@app.route('/login', methods=['GET', 'POST'])
def web_login():
    if request.method == 'GET':
        if current_user.is_authenticated:
            return redirect(url_for('web_feed'))
        return render_template('logIn.html')

    # Procesar Login
    username = request.form.get('inputUserName')
    password = request.form.get('inputPassword')

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('web_feed'))
        else:
            flash("Usuario o contraseña incorrectos")
            return redirect(url_for('landing_page'))
    finally:
        db.close()


@app.route('/signup', methods=['GET', 'POST'])
def web_signup():
    if request.method == 'GET':
        if current_user.is_authenticated:
            return redirect(url_for('profile'))
        return render_template('signUp.html')

    # Procesar Registro
    username = request.form.get('inputUserName')
    email = request.form.get('inputEmail')
    password = request.form.get('inputPassword')

    db = SessionLocal()
    try:
        existing_user = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing_user:
            flash("Error: El nombre de usuario o correo ya están en uso.")
            return redirect(url_for('web_signup'))

        hashed_pw = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_pw)
        db.add(new_user)
        db.commit()

        flash("¡Cuenta creada! Por favor inicia sesión.")
        return redirect(url_for('web_login'))
    except Exception as e:
        db.rollback()
        flash(f"Ocurrió un error: {str(e)}")
        return redirect(url_for('web_signup'))
    finally:
        db.close()


@app.route('/logout')
@login_required
def web_logout():
    logout_user()
    return redirect(url_for('landing_page'))


# --- GESTIÓN DE HILOS Y COMENTARIOS (WEB) ---

@app.route('/create_thread_web', methods=['GET', 'POST'])
@login_required
def create_thread_web():
    db = SessionLocal()
    if request.method == 'GET':
        categories = db.query(Category).all()
        db.close()
        return render_template('createThread.html', categories=categories)

    try:
        new_thread = Thread(
            title=request.form.get('title'),
            content=request.form.get('content'),
            user_id=current_user.id,
            category_id=request.form.get('category_id')
        )
        db.add(new_thread)
        db.commit()
        flash("¡Hilo publicado con éxito!")
        return redirect(url_for('web_feed'))
    except Exception as e:
        db.rollback()
        flash(f"Error al publicar: {str(e)}")
        return redirect(url_for('create_thread_web'))
    finally:
        db.close()


@app.route('/edit_thread/<int:thread_id>', methods=['GET', 'POST'])
@login_required
def edit_thread(thread_id):
    db = SessionLocal()
    try:
        thread = db.query(Thread).filter(Thread.id == thread_id).first()

        if not thread:
            flash("El hilo no existe.")
            return redirect(url_for('web_feed'))

        if thread.user_id != current_user.id:
            flash("No puedes editar el hilo de otra persona.")
            return redirect(url_for('web_feed'))

        if request.method == 'GET':
            categories = db.query(Category).all()
            return render_template('editThread.html', thread=thread, categories=categories)

        # POST
        thread.title = request.form.get('title')
        thread.content = request.form.get('content')
        thread.category_id = request.form.get('category_id')
        db.commit()
        flash("Hilo actualizado correctamente.")
        return redirect(url_for('web_feed'))
    except Exception as e:
        db.rollback()
        flash(f"Error al editar: {str(e)}")
        return redirect(url_for('web_feed'))
    finally:
        db.close()


@app.route('/create_comment_web', methods=['POST'])
@login_required
def create_comment_web():
    thread_id = request.form.get('thread_id')
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
    return redirect(url_for('web_feed'))


@app.route('/edit_comment/<int:comment_id>', methods=['GET', 'POST'])
@login_required
def edit_comment(comment_id):
    db = SessionLocal()
    try:
        comment = db.query(Comment).filter(Comment.id == comment_id).first()
        if not comment:
            flash("El comentario no existe.")
            return redirect(url_for('web_feed'))

        if comment.user_id != current_user.id:
            flash("No puedes editar comentarios de otros.")
            return redirect(url_for('web_feed'))

        if request.method == 'GET':
            return render_template('editComment.html', comment=comment)

        # POST
        new_content = request.form.get('content')
        if not new_content:
            flash("El comentario no puede quedar vacío.")
            return redirect(url_for('edit_comment', comment_id=comment_id))

        comment.content = new_content
        db.commit()
        flash("Comentario actualizado.")
        return redirect(url_for('web_feed'))
    except Exception as e:
        db.rollback()
        flash(f"Error: {str(e)}")
        return redirect(url_for('web_feed'))
    finally:
        db.close()


# ==============================================================================
# 🤖 RUTAS API (Respuestas JSON)
# ==============================================================================

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Se requiere JSON"}), 400

    username = data.get('username')
    password = data.get('password')

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
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


@app.route('/api/signup', methods=['POST'])
def api_signup():
    data = request.get_json()
    if not data or not all(k in data for k in ("username", "email", "password")):
        return jsonify({"error": "Faltan datos"}), 400

    db = SessionLocal()
    try:
        existing_user = db.query(User).filter(
            (User.username == data['username']) | (User.email == data['email'])
        ).first()

        if existing_user:
            return jsonify({"error": "El usuario o email ya existen"}), 400

        new_user = User(
            username=data['username'],
            email=data['email'],
            password=generate_password_hash(data['password'])
        )
        db.add(new_user)
        db.commit()
        return jsonify({"message": "Usuario registrado con éxito"}), 201
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@app.route('/api/users', methods=['GET'])
def get_users():
    db = SessionLocal()
    users = db.query(User).all()
    db.close()
    return jsonify([{"id": u.id, "username": u.username} for u in users])


@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json()
    db = SessionLocal()
    try:
        user = db.query(User).get(user_id)
        if not user:
            return jsonify({"error": "Usuario no encontrado"}), 404

        if 'username' in data: user.username = data['username']
        if 'email' in data: user.email = data['email']
        db.commit()
        return jsonify({"message": "Usuario actualizado"}), 200
    finally:
        db.close()


@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    db = SessionLocal()
    try:
        user = db.query(User).get(user_id)
        if not user:
            return jsonify({"error": "Usuario no encontrado"}), 404
        db.delete(user)
        db.commit()
        return jsonify({"message": "Usuario eliminado"}), 200
    except Exception:
        return jsonify({"error": "No se puede borrar el usuario (tiene actividad)"}), 400
    finally:
        db.close()


@app.route('/api/categories', methods=['GET'])
def get_categories():
    db = SessionLocal()
    cats = db.query(Category).all()
    db.close()
    return jsonify([{"id": c.id, "name": c.name} for c in cats])


@app.route('/api/categories', methods=['POST'])
def create_category():
    data = request.get_json()
    if 'name' not in data:
        return jsonify({"error": "Nombre obligatorio"}), 400

    db = SessionLocal()
    try:
        new_cat = Category(name=data['name'])
        db.add(new_cat)
        db.commit()
        db.refresh(new_cat)
        return jsonify({"id": new_cat.id, "name": new_cat.name, "message": "Creada"}), 201
    finally:
        db.close()


@app.route('/api/threads', methods=['POST'])
def create_thread():
    data = request.get_json()
    if not all(k in data for k in ("title", "content", "user_id", "category_id")):
        return jsonify({"error": "Faltan datos"}), 400

    db = SessionLocal()
    try:
        new_thread = Thread(
            title=data['title'],
            content=data['content'],
            user_id=data['user_id'],
            category_id=data['category_id']
        )
        db.add(new_thread)
        db.commit()
        return jsonify({"message": "Hilo publicado"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        db.close()


@app.route('/api/feed', methods=['GET'])
def get_feed():
    db = SessionLocal()
    threads = db.query(Thread).all()
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


@app.route('/api/threads/<int:thread_id>', methods=['GET'])
def get_single_thread(thread_id):
    db = SessionLocal()
    try:
        thread = db.query(Thread).get(thread_id)
        if not thread:
            return jsonify({"error": "Hilo no encontrado"}), 404
        return jsonify({
            "id": thread.id,
            "title": thread.title,
            "content": thread.content,
            "author": thread.author.username,
            "category": thread.category.name
        })
    finally:
        db.close()


@app.route('/api/threads/<int:thread_id>', methods=['DELETE'])
def delete_thread(thread_id):
    db = SessionLocal()
    try:
        thread = db.query(Thread).get(thread_id)
        if not thread:
            return jsonify({"error": "No encontrado"}), 404
        db.delete(thread)
        db.commit()
        return jsonify({"message": "Eliminado"}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@app.route('/api/comments', methods=['POST'])
def create_comment():
    data = request.get_json()
    if not all(k in data for k in ("content", "user_id", "thread_id")):
        return jsonify({"error": "Faltan datos"}), 400

    db = SessionLocal()
    try:
        new_comment = Comment(
            content=data['content'],
            user_id=data['user_id'],
            thread_id=data['thread_id']
        )
        db.add(new_comment)
        db.commit()
        return jsonify({"message": "Comentario agregado"}), 201
    finally:
        db.close()


@app.route('/api/comments/<int:comment_id>', methods=['DELETE'])
def delete_comment(comment_id):
    db = SessionLocal()
    try:
        comment = db.query(Comment).get(comment_id)
        if not comment:
            return jsonify({"error": "No encontrado"}), 404
        db.delete(comment)
        db.commit()
        return jsonify({"message": "Eliminado"}), 200
    finally:
        db.close()


if __name__ == '__main__':
    app.run(debug=True)