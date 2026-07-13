from extensions import db

class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(10), nullable=False) 
    color = db.Column(db.String(7), default="#000000") 

    transactions = db.relationship('Transaction', backref='category', lazy=True,cascade="all, delete-orphan")
    budgets = db.relationship('Budget', backref='category', lazy=True,cascade="all, delete-orphan")