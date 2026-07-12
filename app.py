# app.py
from flask import Flask
from extensions import db, login_manager
from config import Config
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.admin import admin_bp
from routes.settings import settings_bp  
from routes.category import category_bp
from models.user import User
from routes.api import api_bp
from flask import redirect, url_for,render_template


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # ინიციალიზაცია
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Blueprint-ების რეგისტრაცია
    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(category_bp)

    # create_app()-ის შიგნით:
    @app.route('/')
    def home():
        return redirect(url_for('auth.login'))

    # ბაზის შექმნა ავტომატურად
    with app.app_context():
        db.create_all()

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'),404

    @app.errorhandler(500)
    def internal_error(e):
        return render_template('500.html'),500

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)

