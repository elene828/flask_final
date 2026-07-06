from models.transaction import Transaction
from models.budget import Budget
from extensions import db
from datetime import datetime

def check_budget_status(user_id, category_id, target_date=None):
    if not target_date:
        target_date = datetime.now()
        
    current_month = target_date.month
    current_year = target_date.year
        
    # ბიუჯეტის ძებნა ახალი სქემით
    budget = Budget.query.filter_by(
        user_id=user_id, 
        category_id=category_id, 
        month=current_month, 
        year=current_year
    ).first()
    
    if not budget:
        return {"warning": False, "percentage": 0}

    # იმავე თვისა და წლის აქტიური ხარჯების ჯამი
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