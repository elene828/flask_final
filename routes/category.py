# routes/category.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user
from helpers import custom_login_required
from extensions import db
from models.category import Category
from models.transaction import Transaction  # დაგჭირდება შემოწმებისთვის

category_bp = Blueprint('category', __name__)

# 1. READ - კატეგორიების ჩვენება
@category_bp.route('/categories', methods=['GET'])
@custom_login_required
def index():
    # წამოვიღებთ მხოლოდ ამ მომხმარებლის კატეგორიებს
    user_categories = Category.query.filter_by(user_id=current_user.id).all()
    return render_template('categories.html', categories=user_categories)

# 2. CREATE - კატეგორიის დამატება
@category_bp.route('/category/add', methods=['POST'])
@custom_login_required
def add_category():
    name = request.form.get('name')
    cat_type = request.form.get('type')  # 'income' ან 'expense'

    if not name or not cat_type:
        flash('გთხოვთ შეავსოთ ყველა ველი.', 'warning')
        return redirect(url_for('category.index'))

    # შემოწმება, ხომ არ არსებობს უკვე ამავე სახელის კატეგორია ამ იუზერისთვის
    existing = Category.query.filter_by(user_id=current_user.id, name=name).first()
    if existing:
        flash('ამ სახელწოდების კატეგორია უკვე გაქვთ!', 'warning')
        return redirect(url_for('category.index'))

    new_cat = Category(
        user_id=current_user.id,
        name=name,
        type=cat_type
    )
    db.session.add(new_cat)
    db.session.commit()
    flash('კატეგორია წარმატებით დაემატა!', 'success')
    return redirect(url_for('category.index'))

# 3. UPDATE - კატეგორიის ჩასწორება
@category_bp.route('/category/edit/<int:id>', methods=['POST'])
@custom_login_required
def edit_category(id):
    # უსაფრთხოებისთვის ვეძებთ კატეგორიას ID-ით და თან მომხმარებლის მიხედვით
    cat = Category.query.filter_by(id=id, user_id=current_user.id).first()
    if not cat:
        flash('კატეგორია ვერ მოიძებნა.', 'danger')
        return redirect(url_for('category.index'))

    name = request.form.get('name')
    cat_type = request.form.get('type')

    if not name or not cat_type:
        flash('ველები არ უნდა იყოს ცარიელი.', 'warning')
        return redirect(url_for('category.index'))

    cat.name = name
    cat.type = cat_type
    db.session.commit()
    flash('კატეგორია წარმატებით განახლდა!', 'success')
    return redirect(url_for('category.index'))

# 4. DELETE - კატეგორიის წაშლა
@category_bp.route('/category/delete/<int:id>', methods=['POST'])
@custom_login_required
def delete_category(id):
    cat = Category.query.filter_by(id=id, user_id=current_user.id).first()
    if not cat:
        flash('კატეგორია ვერ მოიძებნა.', 'danger')
        return redirect(url_for('category.index'))

    # 🛑 მნიშვნელოვანი შემოწმება: თუ კატეგორიაში უკვე არის ტრანზაქციები, პირდაპირ არ წავშალოთ
    has_transactions = Transaction.query.filter_by(category_id=id, deleted_at=None).first()
    if has_transactions:
        flash('ამ კატეგორიას ვერ წაშლით, რადგან მასზე მიბმულია ტრანზაქციები!', 'danger')
        return redirect(url_for('category.index'))

    db.session.delete(cat)
    db.session.commit()
    flash('კატეგორია წარმატებით წაიშალა.', 'success')
    return redirect(url_for('category.index'))