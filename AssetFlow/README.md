# AssetFlow - Enterprise Asset & Resource Management System

A complete **Asset & Resource Management ERP** built for the hackathon.

## Features

- **4 Distinct Roles** with proper access control:
  - **Admin** — Full organization control (Departments, Employees, Roles)
  - **Asset Manager** — Registers assets, allocations, approvals
  - **Department Head** — Department assets & approvals
  - **Employee** — View own assets, book resources, raise requests

- **Key Modules**:
  - Asset Registration & Lifecycle Management
  - Allocation & Transfer (prevents double allocation)
  - Resource Booking (overlap validation)
  - Maintenance Approval Workflow
  - Audit Cycles
  - KPI Dashboard with Charts

## Tech Stack

- **Backend**: Python + Flask
- **Database**: SQLAlchemy (SQLite by default, MySQL supported)
- **Frontend**: HTML + CSS + JavaScript
- **Charts**: Chart.js
- **Authentication**: Flask-Login

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt


2. Run the application:

   python run.py

Open your browser and go to:
http://127.0.0.1:5000


Demo Accounts:

Role             Email               Password

Admin            admin@company.com   password
Asset Manager    priya@company.com   password
Department Head  rahul@company.com   password
Employee,        john@company.com    password


Project Structure;

assetflow/
├── app.py
├── run.py
├── config.py
├── models.py
├── requirements.txt
├── static/
│   ├── css/style.css
│   └── js/main.js
└── templates/
    ├── base.html
    ├── login.html
    ├── dashboard.html
    ├── assets.html
    ├── allocation.html
    ├── booking.html
    ├── maintenance.html
    ├── audit.html
    └── reports.html