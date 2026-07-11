from extensions import db
from datetime import datetime

class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(10), nullable=False) # 'income' ან 'expense'
    description = db.Column(db.String(255), nullable=True)
    date = db.Column(db.Date, default=datetime.utcnow().date, nullable=False)
    
    # Soft Delete ფუნქციონალისთვის
    deleted_at = db.Column(db.DateTime, nullable=True)
    