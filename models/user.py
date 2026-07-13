from extensions import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    currency = db.Column(db.String(3), default="GEL") 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin=db.Column(db.Boolean,default=False)

    categories = db.relationship('Category', backref='user', lazy=True,cascade="all, delete-orphan")
    transactions = db.relationship('Transaction', backref='user', lazy=True,cascade="all, delete-orphan")
    budgets = db.relationship('Budget', backref='user', lazy=True,cascade="all, delete-orphan")