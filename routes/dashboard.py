from flask import Blueprint, render_template, request, redirect, url_for, flash, Response
from flask_login import current_user
from datetime import datetime
from helpers import custom_login_required, check_budget_status, perform_conversion
from extensions import db
from models.transaction import Transaction
from models.category import Category
from datetime import datetime
from services import TransactionService, CurrencyConverter
from models.budget import Budget

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/budget/set', methods=['POST'])
@custom_login_required
def set_budget():
    category_id = request.form.get('category_id')
    amount = request.form.get('amount')
    month = request.form.get('month', datetime.utcnow().month)
    year = request.form.get('year', datetime.utcnow().year)

    if not category_id or not amount:
        flash('გთხოვთ მიუთითოთ კატეგორია და თანხა!', 'warning')
        return redirect(url_for('dashboard.index'))

    # ვამოწმებთ, ხომ არ არსებობს უკვე ბიუჯეტი ამ თვისთვის
    existing_budget = Budget.query.filter_by(
        user_id=current_user.id,
        category_id=category_id,
        month=month,
        year=year
    ).first()

    if existing_budget:
        existing_budget.amount = float(amount)
        flash('ბიუჯეტი განახლდა!', 'success')
    else:
        new_budget = Budget(
            user_id=current_user.id,
            category_id=category_id,
            amount=float(amount),
            month=month,
            year=year
        )
        db.session.add(new_budget)
        flash('ბიუჯეტი წარმატებით დაემატა!', 'success')

    db.session.commit()
    return redirect(url_for('dashboard.index'))


@dashboard_bp.route('/dashboard', methods=['GET'])
@custom_login_required
def index():
    user_categories = Category.query.filter_by(user_id=current_user.id).all()
    query = Transaction.query.filter_by(user_id=current_user.id, deleted_at=None)

    # ფილტრების პარამეტრები
    tx_type = request.args.get('type')
    category_id = request.args.get('category_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if tx_type:
        query = query.filter_by(type=tx_type)
    if category_id:
        query = query.filter_by(category_id=category_id)
    if start_date:
        query = query.filter(Transaction.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
    if end_date:
        query = query.filter(Transaction.date <= datetime.strptime(end_date, '%Y-%m-%d').date())

    page=request.args.get('page',1,type=int)
    pagination=query.order_by(Transaction.date.desc()).paginate(page=page,per_page=10,error_out=False)
    transactions=pagination.items

    converter = CurrencyConverter()
    user_currency = current_user.currency or "GEL"

    total_income = 0
    total_expense = 0

    # ტრანზაქციების დინამიური კონვერტაცია მომხმარებლის ვალუტაში საჩვენებლად
    for t in transactions:
        t.display_amount = perform_conversion(t.amount, "GEL", user_currency)

        if t.type == 'income':
            total_income += t.display_amount
        elif t.type == 'expense':
            total_expense += t.display_amount

    balance = round(total_income - total_expense, 2)

    # Top-3 ხარჯი
    expense_totals = {}
    for t in transactions:
        if t.type == 'expense':
            expense_totals[t.category.name] = expense_totals.get(t.category.name, 0) + t.display_amount
    top_3_expenses = sorted(expense_totals.items(), key=lambda x: x[1], reverse=True)[:3]

    # ბიუჯეტის ბეჯები
   # ბიუჯეტის ბეჯები
    budget_badges = {}
    current_date = datetime.utcnow() # მიმდინარე თარიღი
    
    for cat in user_categories:
        if cat.type == 'expense':
            # აქ ვუგზავნით მიმდინარე თარიღს, რომ ივლისის ბიუჯეტი იპოვოს
            status = check_budget_status(current_user.id, cat.id, target_date=current_date)
            
            # ვამოწმებთ, თუ ბიუჯეტი ნაპოვნია და ლიმიტი 0-ზე მეტია
            if status.get("budget_amount", 0) > 0:
                budget_badges[cat.name] = status
                
    return render_template(
        'dashboard.html',
        transactions=transactions,
        balance=balance,
        top_3=top_3_expenses,
        budget_badges=budget_badges,
        categories=user_categories,
        user_currency=user_currency,
        pagination=pagination
    )

@dashboard_bp.route('/transaction/add', methods=['POST'])
@custom_login_required
def add_transaction():
    category_id = request.form.get('category_id')
    tx_type = request.form.get('type')
    amount_raw = request.form.get('amount')
    tx_currency = request.form.get('tx_currency', 'GEL')  # ფასდება ფორმიდან არჩეული ვალუტა
    date_str = request.form.get('date')
    description = request.form.get('description')

    if not category_id or not amount_raw:
        flash('გთხოვთ შეავსოთ სავალდებულო ველები.', 'warning')
        return redirect(url_for('dashboard.index'))

    amount = float(amount_raw)
    user_currency = current_user.currency or "GEL"  
    # ვალუტის გადაყვანა აქაუნთის ბაზისურ ვალუტაში შენახვამდე
    final_amount = perform_conversion(amount, tx_currency, "GEL")
    tx_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else datetime.utcnow().date()

    new_tx = Transaction(
        user_id=current_user.id,
        category_id=int(category_id),
        type=tx_type,
        amount=final_amount,       # ბაზაში მიდის აქაუნთის შესაბამისი თანხა
        date=tx_date,
        description=description
    )

    db.session.add(new_tx)
    db.session.commit()
    display_final = perform_conversion(amount, tx_currency, user_currency)

    if tx_type == 'expense':
        status = check_budget_status(current_user.id, int(category_id))
        if status.get("warning"):
            flash(f"⚠️ გაფრთხილება! ამ კატეგორიის ბიუჯეტის {status['percentage']}% უკვე ათვისებულია!", "warning")
        else:
            flash(f'ხარჯი დაემატა! ({amount} {tx_currency} ➡️ {display_final} {user_currency})', 'success')
    else:
        flash(f'შემოსავალი დაემატა! ({amount} {tx_currency} ➡️ {display_final} {user_currency})', 'success')

    return redirect(url_for('dashboard.index'))

@dashboard_bp.route('/transaction/delete/<int:id>', methods=['POST'])
@custom_login_required
def delete_transaction(id):
    tx = Transaction.query.filter_by(id=id, user_id=current_user.id).first()
    if tx:
        tx.deleted_at = datetime.utcnow()
        db.session.commit()
        flash('ტრანზაქცია წარმატებით წაიშალა.', 'success')
    return redirect(url_for('dashboard.index'))

@dashboard_bp.route('/dashboard/export/csv', methods=['GET'])
@custom_login_required
def export_csv():
    transactions = Transaction.query.filter_by(user_id=current_user.id, deleted_at=None).order_by(Transaction.date.desc()).all()
    service = TransactionService()
    csv_data = service.export_csv(transactions)
    return Response(
        "\ufeff" + csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename=transactions_{current_user.username}.csv"}
    )
@dashboard_bp.route('/transaction/edit/<int:id>', methods=['POST'])
@custom_login_required
def edit_transaction(id):
    tx = Transaction.query.filter_by(id=id, user_id=current_user.id).first()
    if not tx:
        flash('ტრანზაქცია ვერ მოიძებნა.', 'danger')
        return redirect(url_for('dashboard.index'))

    category_id = request.form.get('category_id')
    tx_type = request.form.get('type')
    amount_raw = request.form.get('amount')
    tx_currency = request.form.get('tx_currency', 'GEL')
    date_str = request.form.get('date')
    description = request.form.get('description')

    if not category_id or not amount_raw:
        flash('გთხოვთ შეავსოთ სავალდებულო ველები.', 'warning')
        return redirect(url_for('dashboard.index'))

    amount = float(amount_raw)
    
    # კონვერტაცია ბაზისურ ვალუტაში (GEL) შენახვამდე, ისევე როგორც დამატებისას
    final_amount = perform_conversion(amount, tx_currency, "GEL")

    # მონაცემების განახლება
    tx.category_id = int(category_id)
    tx.type = tx_type
    tx.amount = final_amount
    tx.date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else datetime.utcnow().date()
    tx.description = description

    db.session.commit()
    flash('ტრანზაქცია წარმატებით განახლდა!', 'success')
    return redirect(url_for('dashboard.index'))