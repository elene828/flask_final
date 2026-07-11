# helpers.py
from models.transaction import Transaction
from models.budget import Budget
from extensions import db
from datetime import datetime
from functools import wraps
from flask import redirect, url_for, flash, jsonify, request
from flask_login import current_user

# 1. ბიუჯეტის კონტროლის ფუნქცია
def check_budget_status(user_id, category_id, target_date=None):
    if not target_date:
        target_date = datetime.now()
        
    current_month = target_date.month
    current_year = target_date.year
        
    budget = Budget.query.filter_by(
        user_id=user_id, 
        category_id=category_id, 
        month=current_month, 
        year=current_year
    ).first()
    
    if not budget:
        return {"warning": False, "percentage": 0}

    total_expenses = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id,
        Transaction.category_id == category_id,
        Transaction.type == 'expense',
        Transaction.deleted_at == None,
        db.func.strftime('%m', Transaction.date) == f"{current_month:02d}",
        db.func.strftime('%Y', Transaction.date) == str(current_year)
    ).scalar() or 0.0

    percentage = (total_expenses / budget.amount) * 100
    return {
        "warning": percentage >= 80,
        "percentage": round(percentage, 2),
        "budget_amount": budget.amount,
        "total_expenses": total_expenses
    }

# 2. შენი Custom ავტორიზაციის დეკორატორი (პროექტის მოთხოვნისთვის)
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