from flask import Blueprint, jsonify, request
from flask_login import  current_user
from helpers import custom_login_required,check_budget_status
from extensions import db
from models.transaction import Transaction
from models.category import Category
from datetime import datetime
from services import CurrencyConverter

api_bp = Blueprint('api', __name__, url_prefix='/api')
converter = CurrencyConverter()

@api_bp.route('/transactions', methods=['GET'])
@custom_login_required
def get_transactions():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int) 
    
    
    query = Transaction.query.filter_by(user_id=current_user.id, deleted_at=None)

    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    category_id = request.args.get('category_id')
    tx_type = request.args.get('type')

    if start_date:
        query = query.filter(Transaction.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
    if end_date:
        query = query.filter(Transaction.date <= datetime.strptime(end_date, '%Y-%m-%d').date())
    if category_id:
        query = query.filter_by(category_id=category_id)
    if tx_type:
        query = query.filter_by(type=tx_type)

    paginated_query = query.order_by(Transaction.date.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    transactions_list = []
    for tx in paginated_query.items:
        transactions_list.append({
            "id": tx.id,
            "amount": tx.amount,
            "type": tx.type,
            "category": tx.category.name,
            "date": tx.date.strftime('%Y-%m-%d'),
            "description": tx.description
        })

    return jsonify({
        "transactions": transactions_list,
        "total_pages": paginated_query.pages,
        "current_page": paginated_query.page,
        "total_items": paginated_query.total
    }), 200


@api_bp.route('/transactions', methods=['POST'])
@custom_login_required
def create_transaction():
    data = request.get_json() or {}
    
    if not data.get('category_id') or not data.get('type') or not data.get('amount'):
        return jsonify({"error": "Missing required fields (category_id, type, amount)"}), 400

    category = Category.query.filter_by(id=data['category_id'], user_id=current_user.id).first()
    if not category:
        return jsonify({"error": "Category not found or unauthorized"}), 404

    date_str = data.get('date')
    tx_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else datetime.utcnow().date()

    new_tx = Transaction(
        user_id=current_user.id,
        category_id=data['category_id'],
        type=data['type'],
        amount=float(data['amount']),
        date=tx_date,
        description=data.get('description', '')
    )
    
    db.session.add(new_tx)
    db.session.commit()

    return jsonify({
        "message": "Transaction created successfully",
        "transaction_id": new_tx.id
    }), 201


@api_bp.route('/transactions/<int:id>', methods=['DELETE'])
@custom_login_required
def api_delete_transaction(id):
    tx = Transaction.query.filter_by(id=id, user_id=current_user.id, deleted_at=None).first()
    if not tx:
        return jsonify({"error": "Transaction not found or already deleted"}), 404

    tx.deleted_at = datetime.utcnow() 
    db.session.commit()

    return jsonify({"message": f"Transaction {id} soft deleted successfully"}), 200


@api_bp.route('/balance', methods=['GET'])
@custom_login_required
def get_balance_summary():
    current_date = datetime.utcnow()
    
    summary = converter.get_monthly_summary(current_user.id, current_date.month, current_date.year)
    
    user_currency = current_user.currency
    converted_balance = converter.convert(summary['net_balance'], "GEL", user_currency)

    return jsonify({
        "month": current_date.strftime('%Y-%m'),
        "net_balance_in_gel": summary['net_balance'],
        "converted_balance": converted_balance,
        "currency": user_currency
    }), 200
@api_bp.route('/categories', methods=['GET'])
@custom_login_required
def get_categories():
    categories = Category.query.filter_by(user_id=current_user.id).all()
    categories_list = [{"id": cat.id, "name": cat.name} for cat in categories]
    
    return jsonify({
        "categories": categories_list
    }), 200