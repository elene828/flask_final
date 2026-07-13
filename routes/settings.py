from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user
from helpers import custom_login_required
from extensions import db
from werkzeug.security import generate_password_hash

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/settings', methods=['GET', 'POST'])
@custom_login_required
def index():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        currency = request.form.get('currency', 'GEL')
        new_password = request.form.get('password')

        if username:
            current_user.username = username
        if email:
            current_user.email = email
            
        current_user.currency = currency

        if new_password and new_password.strip() != "":
            current_user.password = generate_password_hash(new_password)

        try:
            db.session.commit()
            flash('პარამეტრები წარმატებით განახლდა!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('შეცდომა მონაცემების შენახვისას. სცადეთ თავიდან.', 'danger')
            
        return redirect(url_for('settings.index'))

    return render_template('settings.html')