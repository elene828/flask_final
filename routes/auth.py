from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from models.user import User
from models.category import Category 
from helpers import custom_login_required,check_budget_status


auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('სისტემაში შესვლა წარმატებით განხორციელდა!', 'success')
            return redirect(url_for('dashboard.index'))
        else:
            flash('არასწორი მომხმარებლის სახელი ან პაროლი.', 'warning')
            
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        currency = request.form.get('currency', 'GEL')
        
        user_exists = User.query.filter((User.username == username) | (User.email == email)).first()
        if user_exists:
            flash('მომხმარებელი ამ სახელით ან ელ-ფოსტით უკვე არსებობს.', 'warning')
            return redirect(url_for('auth.register'))
            
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            currency=currency
        )
        
        db.session.add(new_user)
        db.session.commit()

        default_categories = [
            {"name": "ხელფასი", "type": "income", "color": "#198754"},
            {"name": "საკვები", "type": "expense", "color": "#dc3545"},
            {"name": "ტრანსპორტი", "type": "expense", "color": "#ffc107"},
            {"name": "კომუნალურები", "type": "expense", "color": "#0dcaf0"},
            {"name": "გართობა", "type": "expense", "color": "#6f42c1"}
        ]

        for cat in default_categories:
            new_cat = Category(
                user_id=new_user.id,
                name=cat["name"],
                type=cat["type"],
                color=cat["color"]
            )
            db.session.add(new_cat)

        db.session.commit()
                
        flash('რეგისტრაცია წარმატებით დასრულდა! ახლა შეგიძლიათ შეხვიდეთ სისტემაში.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('register.html')

@auth_bp.route('/logout')
@custom_login_required
def logout():
    logout_user()
    flash('თქვენ გამოხვედით სისტემიდან.', 'success')
    return redirect(url_for('auth.login'))