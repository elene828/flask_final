from models.transaction import Transaction
from models.budget import Budget
from extensions import db
from datetime import datetime
from functools import wraps
from flask import redirect, url_for, flash, jsonify, request
from flask_login import current_user
from models.currency_cache import CurrencyCache

def perform_conversion(amount, from_curr, to_curr):
    if from_curr == to_curr:
        return round(float(amount), 2)
        
    cache = CurrencyCache.get_valid_cache("GEL")
    # თუ cache არ გვაქვს, გამოვიძახოთ CurrencyConverter რომ ახალი მონაცემები მივიღოთ
    if not cache or not cache.rates_json:
        from services import CurrencyConverter
        rates = CurrencyConverter().get_rates()
    else:
        rates = cache.rates_json

    print(f"DEBUG: Converting {amount} from {from_curr} to {to_curr}")
    print(f"DEBUG: Using Rates: {rates}") # <--- ეს გამოიტანს ტერმინალში რეალურ კურსებს
    
    # ავიღოთ კურსები (თუ კლავი არ არსებობს, დავბეჭდოთ გაფრთხილება)
    rate_from = float(rates.get(from_curr, 1.0))
    rate_to = float(rates.get(to_curr, 1.0))
    
    if from_curr not in rates and from_curr != "GEL":
        print(f"WARNING: {from_curr} not found in rates!")
    if to_curr not in rates and to_curr != "GEL":
        print(f"WARNING: {to_curr} not found in rates!")

    amount_in_gel = amount / rate_from
    final_amount = amount_in_gel * rate_to
    
    return round(final_amount, 2)
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