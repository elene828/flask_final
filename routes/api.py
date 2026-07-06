from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from extensions import db
from models.transaction import Transaction
from models.category import Category
from datetime import datetime
from services import CurrencyConverter

api_bp = Blueprint('api', __name__, url_prefix='/api')
converter = CurrencyConverter()

# 1. GET /api/transactions — პაგინირებული სია ფილტრებით
@api_bp.route('/transactions', methods=['GET'])
@login_required
def get_transactions():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int) # დეფოლტად 10 ჩანაწერი გვერდზე
    
    # მხოლოდ აქტიური ტრანზაქციები
    query = Transaction.query.filter_by(user_id=current_user.id, deleted_at=None)

    # ფილტრების წამოღება query params-იდან
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

    # პაგინაცია
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


# 2. POST /api/transactions — ახალი ტრანზაქციის შექმნა
@api_bp.route('/transactions', methods=['POST'])
@login_required
def create_transaction():
    data = request.get_json() or {}
    
    # სავალდებულო ველების ვალიდაცია
    if not data.get('category_id') or not data.get('type') or not data.get('amount'):
        return jsonify({"error": "Missing required fields (category_id, type, amount)"}), 400

    # ვამოწმებთ, ეკუთვნის თუ არა კატეგორია ამ მომხმარებელს
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


# 3. DELETE /api/transactions/<id> — Soft Delete
@api_bp.route('/transactions/<int:id>', methods=['DELETE'])
@login_required
def api_delete_transaction(id):
    tx = Transaction.query.filter_by(id=id, user_id=current_user.id, deleted_at=None).first()
    if not tx:
        return jsonify({"error": "Transaction not found or already deleted"}), 404

    tx.deleted_at = datetime.utcnow() # Soft delete ლოგიკა
    db.session.commit()

    return jsonify({"message": f"Transaction {id} soft deleted successfully"}), 200


# 4. GET /api/balance — მიმდინარე თვის რეზიუმე (ბალანსი)
@api_bp.route('/balance', methods=['GET'])
@login_required
def get_balance_summary():
    current_date = datetime.utcnow()
    
    # OOP სერვისის გამოძახება
    summary = converter.get_monthly_summary(current_user.id, current_date.month, current_date.year)
    
    # ვალუტის კონვერტაცია მომხმარებლის დეფოლტ ვალუტაზე (მაგ. თუ USD აქვს არჩეული)
    user_currency = current_user.currency # ველი ბაზიდან
    converted_balance = converter.convert(summary['net_balance'], "GEL", user_currency)

    return jsonify({
        "month": current_date.strftime('%Y-%m'),
        "net_balance_in_gel": summary['net_balance'],
        "converted_balance": converted_balance,
        "currency": user_currency
    }), 200
# 5. GET /api/categories — მომხმარებლის პირადი კატეგორიების სია
@api_bp.route('/categories', methods=['GET'])
@login_required
def get_categories():
    categories = Category.query.filter_by(user_id=current_user.id).all()
    categories_list = [{"id": cat.id, "name": cat.name} for cat in categories]
    
    return jsonify({
        "categories": categories_list
    }), 200