from flask import Blueprint,render_template,redirect,url_for,flash
from models.user import User
from extensions import db
from helpers import admin_required,custom_login_required

admin_bp=Blueprint('admin',__name__,url_prefix='/admin')

@admin_bp.route('/')
@custom_login_required
@admin_required
def index():
    users=User.query.all()
    return render_template('admin.html',users=users)

@admin_bp.route('/user/delete/<int:id>',methods=['POST'])
@custom_login_required
@admin_required
def delete_user(id):
    user=User.query.get(id)
    if user:
        if user.is_admin:
            flash('ადმინის ჭაშლა შეუძლებელია!','danger')
        else:
            db.session.delete(user)
            db.session.commit()
            flash('მომხმარებელი წარმატებით წაიშალა!','success')
    return redirect(url_for('admin.index'))
