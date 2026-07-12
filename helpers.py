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
    
    # ავიღოთ კურსები (თუ კლავი არ არსებობს, დავბეჭდოთ გაფრთხილება)
    rate_from = float(rates.get(from_curr, 1.0))
    rate_to = float(rates.get(to_curr, 1.0))
    
    amount_in_gel = amount / rate_from
    final_amount = amount_in_gel * rate_to
    
    return round(final_amount, 2)
# 1. ბიუჯეტის კონტროლის ფუნქცია
def check_budget_status(user_id, category_id, target_date=None):
    if not target_date:
        target_date = datetime.utcnow()
    
    budget = Budget.query.filter_by(
        user_id=user_id, 
        category_id=category_id, 
        month=target_date.month, 
        year=target_date.year
    ).first()

    # თუ ბიუჯეტი არ არსებობს, დააბრუნე 0-ები
    if not budget:
        return {"warning": False, "percentage": 0, "total_expenses": 0, "budget_amount": 0}

    # 1. აუცილებლად დააინიციალიზეთ ცვლადი 0-ით
    total_expenses = 0 
    
    transactions = Transaction.query.filter(
        Transaction.user_id == user_id,
        Transaction.category_id == category_id,
        Transaction.type == 'expense',
        Transaction.deleted_at == None,
        db.func.strftime('%m', Transaction.date) == f"{target_date.month:02d}",
        db.func.strftime('%Y', Transaction.date) == str(target_date.year)
    ).all()

    # 2. ხარჯების დათვლა
    for tx in transactions:
        tx_curr = getattr(tx, 'currency', 'GEL')
        total_expenses += perform_conversion(tx.amount, tx_curr, "EUR")

    # 3. პროცენტის დათვლა (დაიცავით თავი ნულზე გაყოფისგან)
    percentage = (total_expenses / budget.amount * 100) if budget.amount > 0 else 0
    
    return {
        "warning": percentage >= 80,
        "percentage": round(percentage, 2),
        "total_expenses": round(total_expenses, 2),
        "budget_amount": budget.amount
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