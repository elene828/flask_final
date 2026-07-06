# models/exchange_rate.py
from extensions import db
from datetime import datetime

class ExchangeRate(db.Model):
    __tablename__ = 'exchange_rates'

    id = db.Column(db.Integer, primary_key=True)
    base = db.Column(db.String(10), nullable=False)        # რომელი ვალუტიდან (მაგ: GEL)
    target = db.Column(db.String(10), nullable=False)      # რომელ ვალუტაში (მაგ: USD)
    rate = db.Column(db.Float, nullable=False)             # კურსი
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)