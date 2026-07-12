from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    # Stored as a Werkzeug hash (not plaintext)
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), default='Employee')
    department = db.Column(db.String(100))
    status = db.Column(db.String(20), default='Active')

    # Password reset (demo-friendly; token stored as hash)
    reset_token_hash = db.Column(db.String(255), nullable=True)
    reset_expires_at = db.Column(db.DateTime, nullable=True)


class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    head = db.Column(db.String(100))
    parent_department = db.Column(db.String(100))
    status = db.Column(db.String(20), default='Active')
    description = db.Column(db.Text, nullable=True)


class AssetCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    warranty_period = db.Column(db.String(50), nullable=True)


class Asset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tag = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))
    serial = db.Column(db.String(50))
    description = db.Column(db.Text, nullable=True)
    condition = db.Column(db.String(50), default='Good')
    acquisition_cost = db.Column(db.String(50), nullable=True)
    is_shared = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(50), default='Available')
    location = db.Column(db.String(100))
    allocated_to = db.Column(db.String(100))
    expected_return = db.Column(db.DateTime)
    acquisition_date = db.Column(db.DateTime, default=datetime.utcnow)

    # Transfer workflow (used by Dashboard KPI “Pending Transfers”)
    transfer_status = db.Column(db.String(20), default='None')  # None|Pending|Completed
    transfer_requested_to = db.Column(db.String(100), nullable=True)
    transfer_requested_by = db.Column(db.String(100), nullable=True)
    transfer_requested_at = db.Column(db.DateTime, nullable=True)


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    resource = db.Column(db.String(100), nullable=False)
    booked_by = db.Column(db.String(100))
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='Upcoming')

class Maintenance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    asset_tag = db.Column(db.String(50))
    issue = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), default='Medium')
    status = db.Column(db.String(50), default='Pending')
    requested_by = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)