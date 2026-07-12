from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from models import db, User, Asset
from config import Config
from datetime import datetime

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def is_admin():
    return current_user.is_authenticated and current_user.role == 'Admin'

def is_asset_manager():
    return current_user.is_authenticated and current_user.role in ['Admin', 'AssetManager']

def is_department_head():
    return current_user.is_authenticated and current_user.role in ['Admin', 'DepartmentHead']

def is_employee():
    return current_user.is_authenticated and current_user.role in ['Admin', 'Employee']



# ===================== ROUTES =====================
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Simple (non-WTF) login form used by login.html
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid credentials. Use password: password')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    stats = {
        'available': Asset.query.filter_by(status='Available').count(),
        'allocated': Asset.query.filter_by(status='Allocated').count(),
        'maintenance': Asset.query.filter_by(status='Under Maintenance').count(),
    }
    recent_assets = Asset.query.order_by(Asset.id.desc()).limit(5).all()
    return render_template('dashboard.html', stats=stats, recent_assets=recent_assets, user_role=current_user.role)

@app.route('/assets')
@login_required
def assets():
    if is_asset_manager():
        all_assets = Asset.query.all()
    else:
        all_assets = Asset.query.filter_by(allocated_to=current_user.name).all()
    return render_template('assets.html', assets=all_assets, user_role=current_user.role)

@app.route('/assets/create', methods=['POST'])
@login_required
def create_asset():
    if not is_asset_manager():
        abort(403)
    tag = request.form.get('tag') or f"AF-{datetime.now().strftime('%Y%m%d%H%M')}"
    asset = Asset(
        tag=tag,
        name=request.form['name'],
        category=request.form['category'],
        location=request.form.get('location'),
        status='Available'
    )
    db.session.add(asset)
    db.session.commit()
    flash('Asset created successfully!', 'success')
    return redirect(url_for('assets'))

@app.route('/assets/<int:id>/update', methods=['POST'])
@login_required
def update_asset(id):
    if not is_asset_manager():
        abort(403)
    asset = Asset.query.get_or_404(id)
    asset.status = request.form.get('status', asset.status)
    asset.location = request.form.get('location', asset.location)
    db.session.commit()
    flash('Asset updated!', 'success')
    return redirect(url_for('assets'))

@app.route('/assets/<int:id>/delete', methods=['POST'])
@login_required
def delete_asset(id):
    if not is_admin():
        abort(403)
    asset = Asset.query.get_or_404(id)
    db.session.delete(asset)
    db.session.commit()
    flash('Asset deleted.', 'success')
    return redirect(url_for('assets'))

@app.route('/allocation')
@login_required
def allocation():
    assets = Asset.query.all()
    return render_template('allocation.html', assets=assets, user_role=current_user.role)

@app.route('/booking')
@login_required
def booking():
    return render_template('booking.html', user_role=current_user.role)

@app.route('/maintenance')
@login_required
def maintenance():
    return render_template('maintenance.html', user_role=current_user.role)

@app.route('/audit')
@login_required
def audit():
    return render_template('audit.html', user_role=current_user.role)

@app.route('/reports')
@login_required
def reports():
    return render_template('reports.html', user_role=current_user.role)

if __name__ == '__main__':
    app.run(debug=True, port=5000)