from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from persistence.db import Base  # Importamos la Base de tu archivo db.py

from flask_login import UserMixin

# 1. ENTIDAD CATEGORY
class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True)

    # Relación: Una categoría tiene muchos threads
    threads = relationship('Thread', back_populates='category')

    @classmethod
    def get_all(cls, session):
        return session.query(cls).all()

    @classmethod
    def create(cls, session, name):
        new_cat = cls(name=name)
        session.add(new_cat)
        session.commit()
        session.refresh(new_cat)
        return new_cat


# 2. ENTIDAD USER
class User(UserMixin, Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(80), nullable=False, unique=True)
    email = Column(String(120), nullable=False, unique=True)
    password = Column(String(255), nullable=False)

    # Relaciones
    threads = relationship('Thread', back_populates='author')
    comments = relationship('Comment', back_populates='author')

    @classmethod
    def get_by_id(cls, session, user_id):
        return session.query(cls).get(int(user_id))

    @classmethod
    def get_by_username(cls, session, username):
        return session.query(cls).filter(cls.username == username).first()

    @classmethod
    def get_by_username_or_email(cls, session, username, email):
        return session.query(cls).filter((cls.username == username) | (cls.email == email)).first()

    @classmethod
    def get_all(cls, session):
        return session.query(cls).all()

    @classmethod
    def create(cls, session, username, email, password):
        new_user = cls(username=username, email=email, password=password)
        session.add(new_user)
        session.commit()
        return new_user

    @classmethod
    def delete(cls, session, user_instance):
        session.delete(user_instance)
        session.commit()


# 3. ENTIDAD THREAD (Hilo)
class Thread(Base):
    __tablename__ = 'threads'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Claves Foráneas
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)

    # Relaciones
    author = relationship('User', back_populates='threads')
    category = relationship('Category', back_populates='threads')
    comments = relationship('Comment', back_populates='thread')

    @classmethod
    def get_all_ordered(cls, session):
        return session.query(cls).order_by(cls.created_at.desc()).all()

    @classmethod
    def get_by_id(cls, session, thread_id):
        return session.query(cls).get(thread_id)

    @classmethod
    def get_all(cls, session):
        return session.query(cls).all()

    @classmethod
    def create(cls, session, title, content, user_id, category_id):
        new_thread = cls(title=title, content=content, user_id=user_id, category_id=category_id)
        session.add(new_thread)
        session.commit()
        return new_thread

    @classmethod
    def delete(cls, session, thread_instance):
        session.delete(thread_instance)
        session.commit()


# 4. ENTIDAD COMMENT
class Comment(Base):
    __tablename__ = 'comments'

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Claves Foráneas
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    thread_id = Column(Integer, ForeignKey('threads.id'), nullable=False)

    # Relaciones
    author = relationship('User', back_populates='comments')
    thread = relationship('Thread', back_populates='comments')

    @classmethod
    def create(cls, session, content, user_id, thread_id):
        new_comment = cls(content=content, user_id=user_id, thread_id=thread_id)
        session.add(new_comment)
        session.commit()
        return new_comment

    @classmethod
    def get_by_id(cls, session, comment_id):
        return session.query(cls).filter(cls.id == comment_id).first()

    @classmethod
    def delete(cls, session, comment_instance):
        session.delete(comment_instance)
        session.commit()