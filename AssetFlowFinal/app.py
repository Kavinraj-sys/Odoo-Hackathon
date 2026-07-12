from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Asset, Department, AssetCategory, Maintenance, Booking
from config import Config
from datetime import datetime, timedelta
import secrets
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash



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


def parse_optional_datetime(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


# ===================== ROUTES =====================
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Simple login form used by login.html
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid credentials. Check your email/password.')

    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = (request.form.get('name') or '').strip()
        email = (request.form.get('email') or '').strip().lower()
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not name or not email or not password:
            flash('All fields are required.', 'danger')
            return render_template('signup.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('signup.html')

        existing = User.query.filter_by(email=email).first()
        if existing:
            flash('Email already registered. Please sign in.', 'warning')
            return redirect(url_for('login'))

        user = User(
            email=email,
            password=generate_password_hash(password),
            name=name,
            role='Employee'
        )
        db.session.add(user)
        db.session.commit()

        flash('Account created. You can now sign in.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = (request.form.get('email') or '').strip().lower()
        user = User.query.filter_by(email=email).first()

        # Always respond similarly to avoid account enumeration.
        if user:
            token = secrets.token_urlsafe(32)
            token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
            user.reset_token_hash = token_hash
            user.reset_expires_at = datetime.utcnow() + timedelta(hours=1)
            db.session.commit()

            # Demo-friendly: show the reset link/token.
            reset_url = url_for('reset_password', token=token, _external=True)
            flash(f'Reset link (demo): {reset_url}', 'success')

        flash('If an account exists for that email, a reset link has been generated.', 'info')
        return redirect(url_for('login'))

    return render_template('forgot_password.html')


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
    user = User.query.filter_by(reset_token_hash=token_hash).first()

    if not user or not user.reset_expires_at or user.reset_expires_at < datetime.utcnow():
        flash('Reset link is invalid or expired.', 'danger')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        if not password or password != confirm_password:
            flash('Passwords must match.', 'danger')
            return render_template('reset_password.html')

        user.password = generate_password_hash(password)
        user.reset_token_hash = None
        user.reset_expires_at = None
        db.session.commit()

        flash('Password updated. Please sign in.', 'success')
        return redirect(url_for('login'))

    return render_template('reset_password.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/')
@login_required
def dashboard():
    now = datetime.utcnow()
    today = now.date()

    # KPI cards
    available = Asset.query.filter_by(status='Available').count()
    allocated = Asset.query.filter_by(status='Allocated').count()
    maintenance_today = Maintenance.query.filter(
        Maintenance.status.in_(['Pending', 'Approved', 'In Progress', 'Pending Approval', 'Pending review']),
        db.func.date(Maintenance.created_at) == str(today)
    ).count()

    active_bookings = Booking.query.filter(
        Booking.status == 'Confirmed',
        Booking.start_time <= now,
        Booking.end_time >= now,
    ).count()

    pending_transfers = Asset.query.filter(Asset.transfer_status == 'Pending').count()

    # Upcoming / Overdue returns (expected_return based)
    upcoming_returns = Asset.query.filter(
        Asset.expected_return != None,
        Asset.expected_return >= now,
        Asset.status == 'Allocated'
    ).count()

    overdue_returns = Asset.query.filter(
        Asset.expected_return != None,
        Asset.expected_return < now,
        Asset.status == 'Allocated'
    ).count()

    stats = {
        'available': available,
        'allocated': allocated,
        'maintenance_today': maintenance_today,
        'active_bookings': active_bookings,
        'pending_transfers': pending_transfers,
        'upcoming_returns': upcoming_returns,
        'overdue_returns': overdue_returns,
    }

    recent_assets = Asset.query.order_by(Asset.id.desc()).limit(5).all()
    return render_template('dashboard.html', stats=stats, recent_assets=recent_assets, user_role=current_user.role)


@app.route('/assets')
@login_required
def assets():
    if is_asset_manager():
        all_assets = Asset.query.order_by(Asset.id.desc()).all()
    else:
        all_assets = Asset.query.filter_by(allocated_to=current_user.name).order_by(Asset.id.desc()).all()

    categories = AssetCategory.query.order_by(AssetCategory.name.asc()).all()
    departments = Department.query.filter_by(status='Active').order_by(Department.name.asc()).all()
    return render_template('assets.html', assets=all_assets, categories=categories, departments=departments, user_role=current_user.role)

@app.route('/assets/create', methods=['POST'])
@login_required
def create_asset():
    if not is_asset_manager():
        abort(403)

    tag = (request.form.get('tag') or '').strip() or f"AF-{datetime.now().strftime('%Y%m%d%H%M')}"
    asset = Asset(
        tag=tag,
        name=(request.form.get('name') or '').strip(),
        category=(request.form.get('category') or '').strip(),
        serial=(request.form.get('serial') or '').strip(),
        description=(request.form.get('description') or '').strip(),
        condition=(request.form.get('condition') or 'Good').strip(),
        acquisition_cost=(request.form.get('acquisition_cost') or '').strip(),
        location=(request.form.get('location') or '').strip(),
        is_shared=request.form.get('is_shared') == 'on',
        acquisition_date=parse_optional_datetime(request.form.get('acquisition_date')),
        status='Available',
    )
    if not asset.name:
        flash('Asset name is required.', 'danger')
        return redirect(url_for('assets'))

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
    asset.tag = (request.form.get('tag') or asset.tag).strip()
    asset.name = (request.form.get('name') or asset.name).strip()
    asset.category = (request.form.get('category') or asset.category).strip()
    asset.serial = (request.form.get('serial') or asset.serial).strip()
    asset.description = (request.form.get('description') or asset.description).strip()
    asset.condition = (request.form.get('condition') or asset.condition).strip() or asset.condition
    asset.acquisition_cost = (request.form.get('acquisition_cost') or asset.acquisition_cost).strip()
    asset.location = (request.form.get('location') or asset.location).strip()
    asset.is_shared = request.form.get('is_shared') == 'on'
    asset.status = request.form.get('status') or asset.status
    asset.acquisition_date = parse_optional_datetime(request.form.get('acquisition_date')) or asset.acquisition_date
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

@app.route('/allocation', methods=['GET', 'POST'])
@login_required
def allocation():
    assets = Asset.query.order_by(Asset.id.desc()).all()

    if request.method == 'POST':
        asset_id = request.form.get('asset_id')
        target_name = request.form.get('target_employee')
        expected_return_str = request.form.get('expected_return')

        asset = Asset.query.get_or_404(int(asset_id))

        # Parse expected return if provided
        expected_return = None
        if expected_return_str:
            try:
                expected_return = datetime.fromisoformat(expected_return_str)
            except ValueError:
                expected_return = None

        if asset.allocated_to and asset.status == 'Allocated':
            # Conflict -> create transfer request
            asset.transfer_status = 'Pending'
            asset.transfer_requested_to = target_name
            asset.transfer_requested_by = current_user.name
            asset.transfer_requested_at = datetime.utcnow()
            db.session.commit()
            flash(f"Asset is currently held by {asset.allocated_to}. Transfer requested.", 'warning')
            return redirect(url_for('allocation'))

        # Allocate directly (available)
        asset.allocated_to = target_name
        asset.expected_return = expected_return
        asset.status = 'Allocated'
        asset.transfer_status = 'None'
        asset.transfer_requested_to = None
        asset.transfer_requested_by = None
        asset.transfer_requested_at = None
        db.session.commit()
        flash('Asset allocated successfully.', 'success')
        return redirect(url_for('allocation'))

    return render_template('allocation.html', assets=assets, user_role=current_user.role)


@app.route('/booking', methods=['GET', 'POST'])
@login_required
def booking():
    now = datetime.utcnow()
    if request.method == 'POST':
        resource = (request.form.get('resource') or '').strip()
        start_time_str = request.form.get('start_time')
        end_time_str = request.form.get('end_time')

        if not resource or not start_time_str or not end_time_str:
            flash('Resource, start time and end time are required.', 'danger')
            return redirect(url_for('booking'))

        try:
            start_time = datetime.fromisoformat(start_time_str)
            end_time = datetime.fromisoformat(end_time_str)
        except ValueError:
            flash('Invalid datetime format.', 'danger')
            return redirect(url_for('booking'))

        if end_time <= start_time:
            flash('End time must be after start time.', 'danger')
            return redirect(url_for('booking'))

        # Overlap validation (no overlaps)
        overlap = Booking.query.filter(
            Booking.resource == resource,
            Booking.status.in_(['Upcoming', 'Ongoing']),
            Booking.start_time < end_time,
            Booking.end_time > start_time,
        ).first()

        if overlap:
            flash('Requested slot overlaps an existing booking. Choose a different time.', 'warning')
            return redirect(url_for('booking'))

        status = 'Upcoming'
        if start_time <= now <= end_time:
            status = 'Ongoing'

        booking = Booking(
            resource=resource,
            booked_by=current_user.name,
            start_time=start_time,
            end_time=end_time,
            status=status,
        )
        db.session.add(booking)
        db.session.commit()

        flash('Booking confirmed.', 'success')
        return redirect(url_for('booking'))

    # Keep statuses fresh
    bookings = Booking.query.order_by(Booking.start_time.asc()).all()
    for b in bookings:
        if b.start_time <= now <= b.end_time and b.status == 'Upcoming':
            b.status = 'Ongoing'
        elif now > b.end_time and b.status in ['Upcoming', 'Ongoing']:
            b.status = 'Completed'
    db.session.commit()

    return render_template('booking.html', bookings=bookings, user_role=current_user.role)


@app.route('/maintenance', methods=['GET', 'POST'])
@login_required
def maintenance():
    if request.method == 'POST':
        # Raise request
        asset_tag = request.form.get('asset_tag')
        issue = request.form.get('issue')
        priority = request.form.get('priority', 'Medium')

        if not asset_tag or not issue:
            flash('Asset and issue description are required.', 'danger')
            return redirect(url_for('maintenance'))

        maint = Maintenance(
            asset_tag=asset_tag,
            issue=issue,
            priority=priority,
            status='Pending',
            requested_by=current_user.name,
        )
        db.session.add(maint)
        db.session.commit()
        flash('Maintenance request raised.', 'success')
        return redirect(url_for('maintenance'))

    requests_q = Maintenance.query.order_by(Maintenance.created_at.desc()).all()
    assets = Asset.query.order_by(Asset.id.asc()).all()

    # Asset status auto-update on approve/reject happens in approval endpoints below.
    return render_template('maintenance.html', maintenance_requests=requests_q, assets=assets, user_role=current_user.role)

@app.route('/maintenance/<int:req_id>/<action>', methods=['POST'])
@login_required
def maintenance_action(req_id, action):
    if not is_asset_manager():
        abort(403)

    maint = Maintenance.query.get_or_404(req_id)
    asset = Asset.query.filter_by(tag=maint.asset_tag).first()

    if action == 'approve':
        maint.status = 'Approved'
        # Asset auto-updates to Under Maintenance on approval
        if asset:
            asset.status = 'Under Maintenance'
            db.session.commit()
        db.session.commit()
        flash('Maintenance approved. Asset marked Under Maintenance.', 'success')
    elif action == 'reject':
        maint.status = 'Rejected'
        db.session.commit()
        flash('Maintenance rejected.', 'warning')
    else:
        abort(400)

    return redirect(url_for('maintenance'))


@app.route('/audit')
@login_required
def audit():
    return render_template('audit.html', user_role=current_user.role)

@app.route('/reports')
@login_required
def reports():
    return render_template('reports.html', user_role=current_user.role)


@app.route('/organization-setup', methods=['GET', 'POST'])
@login_required
def organization_setup():
    if not is_admin():
        abort(403)

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'create_department':
            name = (request.form.get('name') or '').strip()
            if name:
                department = Department(name=name, head=(request.form.get('head') or '').strip(), parent_department=(request.form.get('parent_department') or '').strip(), status=(request.form.get('status') or 'Active').strip(), description=(request.form.get('description') or '').strip())
                db.session.add(department)
                db.session.commit()
                flash('Department created.', 'success')
            else:
                flash('Department name is required.', 'danger')

        elif action == 'update_department':
            department_id = request.form.get('department_id')
            if department_id:
                department = Department.query.get_or_404(int(department_id))
                department.name = (request.form.get('name') or department.name).strip()
                department.head = (request.form.get('head') or '').strip() or department.head
                department.parent_department = (request.form.get('parent_department') or '').strip() or department.parent_department
                department.status = (request.form.get('status') or department.status).strip() or department.status
                department.description = (request.form.get('description') or '').strip() or department.description
                db.session.commit()
                flash('Department updated.', 'success')

        elif action == 'create_category':
            name = (request.form.get('name') or '').strip()
            if name:
                category = AssetCategory(name=name, description=(request.form.get('description') or '').strip(), warranty_period=(request.form.get('warranty_period') or '').strip())
                db.session.add(category)
                db.session.commit()
                flash('Asset category created.', 'success')
            else:
                flash('Category name is required.', 'danger')

        elif action == 'update_category':
            category_id = request.form.get('category_id')
            if category_id:
                category = AssetCategory.query.get_or_404(int(category_id))
                category.name = (request.form.get('name') or category.name).strip()
                category.description = (request.form.get('description') or '').strip() or category.description
                category.warranty_period = (request.form.get('warranty_period') or '').strip() or category.warranty_period
                db.session.commit()
                flash('Asset category updated.', 'success')

        elif action == 'update_employee':
            user_id = request.form.get('user_id')
            if user_id:
                user = User.query.get_or_404(int(user_id))
                user.department = (request.form.get('department') or '').strip() or user.department
                user.status = (request.form.get('status') or user.status).strip() or user.status
                db.session.commit()
                flash('Employee updated.', 'success')

        else:
            abort(400)

        return redirect(url_for('organization_setup'))

    departments = Department.query.order_by(Department.name.asc()).all()
    categories = AssetCategory.query.order_by(AssetCategory.name.asc()).all()
    employees = User.query.order_by(User.name.asc()).all()
    return render_template('organization_setup.html', departments=departments, categories=categories, employees=employees, user_role=current_user.role)


@app.route('/employees', methods=['GET'])
@login_required
def employee_directory():
    return redirect(url_for('organization_setup'))


@app.route('/employees/promote-department-head', methods=['POST'])
@login_required
def promote_department_head():
    if not is_admin():
        abort(403)
    user_id = request.form.get('user_id')
    user = User.query.get_or_404(int(user_id))
    user.role = 'DepartmentHead'
    db.session.commit()
    flash(f'{user.name} promoted to Department Head.', 'success')
    return redirect(url_for('employee_directory'))


@app.route('/employees/promote-asset-manager', methods=['POST'])
@login_required
def promote_asset_manager():
    if not is_admin():
        abort(403)
    user_id = request.form.get('user_id')
    user = User.query.get_or_404(int(user_id))
    user.role = 'AssetManager'
    db.session.commit()
    flash(f'{user.name} promoted to Asset Manager.', 'success')
    return redirect(url_for('employee_directory'))


if __name__ == '__main__':
    app.run(debug=True, port=5000)

