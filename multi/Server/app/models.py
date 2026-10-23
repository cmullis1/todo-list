# app/models.py

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(20), unique=True, nullable=False, index=True)
    password = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    token = db.Column(db.String(36), unique=True, nullable=True)  # UUID4 tokens
    token_expiration = db.Column(db.String, nullable=True)  # ISO formatted datetime string
    tasks = db.relationship("Task", back_populates="assigned_user", cascade="all, delete-orphan")

class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    task_name = db.Column(db.String, nullable=False)
    assigned_to = db.Column(db.String, db.ForeignKey('users.username', ondelete='CASCADE'), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    due_date = db.Column(db.String, nullable=True)
    due_time = db.Column(db.String, nullable=True)
    priority = db.Column(db.String, default="Normal")
    details = db.Column(db.String, nullable=True)
    assigned_user = db.relationship("User", back_populates="tasks")
