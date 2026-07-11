# routes/finance.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import  current_user
from extensions import db
from models.transaction import Transaction
from models.category import Category
from helpers import check_budget_status
from datetime import datetime
from helpers import custom_login_required,check_budget_status


finance_bp = Blueprint('finance', __name__)

# ტრანზაქციის დამატება
@finance_bp.route('/transaction/add', methods=['POST'])
@custom_login_required
def add_transaction():
    category_id = request.form.get('category_id')
    tx_type = request.form.get('type') # 'income' ან 'expense'
    amount = float(request.form.get('amount'))
    date_str = request.form.get('date')
    description = request.form.get('description')
    
    date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else datetime.utcnow().date()

    new_tx = Transaction(
        user_id=current_user.id,
        category_id=category_id,
        type=tx_type,
        amount=amount,
        date=date,
        description=description
    )
    db.session.add(new_tx)
    db.session.commit()

    # თუ ხარჯია, ვამოწმებთ ბიუჯეტის გადაცილებას
    if tx_type == 'expense':
        budget_status = check_budget_status(current_user.id, category_id, date.strftime('%Y-%m'))
        if budget_status['warning']:
            flash(f"გაფრთხილება! ამ კატეგორიის ბიუჯეტის {budget_status['percentage']}% უკვე ათვისებულია!", "warning")

    return redirect(url_for('dashboard.index'))

# Soft Delete ფუნქციონალი
@finance_bp.route('/transaction/delete/<int:id>', methods=['POST'])
@custom_login_required
def delete_transaction(id):
    tx = Transaction.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    tx.deleted_at = datetime.utcnow() # ფიზიკურად არ იშლება, ენიჭება დრო
    db.session.commit()
    flash("ტრანზაქცია წარმატებით წაიშალა (Soft Delete).", "success")
    return redirect(url_for('dashboard.index'))