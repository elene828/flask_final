from extensions import db
from datetime import datetime, timedelta

class CurrencyCache(db.Model):
    __tablename__ = 'currency_cache'

    id = db.Column(db.Integer, primary_key=True)
    base_currency = db.Column(db.String(3), default="GEL", nullable=False)
    rates_json = db.Column(db.JSON, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def get_valid_cache(cls, base="GEL"):
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        return cls.query.filter(
            cls.base_currency == base,
            cls.updated_at >= one_hour_ago
        ).first()