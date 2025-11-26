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