from models.transaction import Transaction
from models.budget import Budget
from extensions import db
from functools import wraps
from datetime import datetime 
from flask import redirect, url_for, flash, jsonify, request
from flask_login import current_user
from models.currency_cache import CurrencyCache
from services import CurrencyConverter

converter = CurrencyConverter()

def check_budget_status(user_id, category_id, target_date=None):
    if not target_date:
        target_date = datetime.utcnow()
    
    budget = Budget.query.filter_by(
        user_id=user_id, 
        category_id=category_id, 
        month=target_date.month, 
        year=target_date.year
    ).first()

    if not budget:
        return {"warning": False, "percentage": 0, "total_expenses": 0, "budget_amount": 0}

    total_expenses = 0 
    
    transactions = Transaction.query.filter(
        Transaction.user_id == user_id,
        Transaction.category_id == category_id,
        Transaction.type == 'expense',
        Transaction.deleted_at == None,
        db.func.strftime('%m', Transaction.date) == f"{target_date.month:02d}",
        db.func.strftime('%Y', Transaction.date) == str(target_date.year)
    ).all()

    for tx in transactions:
        tx_curr = getattr(tx, 'currency', 'GEL')
        total_expenses += converter.convert(tx.amount, tx_curr, "EUR")

    percentage = (total_expenses / budget.amount * 100) if budget.amount > 0 else 0
    
    return {
        "warning": percentage >= 80,
        "percentage": round(percentage, 2),
        "total_expenses": round(total_expenses, 2),
        "budget_amount": budget.amount
    }

def custom_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.path.startswith('/api/'):
                return jsonify({"error": "Unauthorized. Please log in."}), 401
            flash('გთხოვთ გაიაროთ ავტორიზაცია.', 'warning')
            return redirect(url_for('auth.login')) 
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args,**kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('თქვენ არ გაქვთ ადმინის უფლებები.','danger')
            return redirect(url_for('dashboard.index'))
        return f(*args,**kwargs)
    return decorated_function