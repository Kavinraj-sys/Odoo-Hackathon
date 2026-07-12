from app import app, db
from models import User, Asset, Department, AssetCategory

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        print("Seeding/ensuring demo data...")

        # Create-only: do not overwrite existing users/passwords.
        # This ensures demo accounts work even if the DB already contains some users.
        from werkzeug.security import generate_password_hash
        demo_users = [
            User(email='admin@company.com', password=generate_password_hash('password'), name='Admin User', role='Admin'),
            User(email='priya@company.com', password=generate_password_hash('password'), name='Priya Shah', role='AssetManager'),
            User(email='rahul@company.com', password=generate_password_hash('password'), name='Rahul Verma', role='DepartmentHead'),
            # Correct email kept:
            User(email='john@company.com', password=generate_password_hash('password'), name='John Doe', role='Employee'),
            # Also add the exact typo requested to make login work:
            User(email='john@comapny.com', password=generate_password_hash('password'), name='John Doe (typo email)', role='Employee'),
        ]


        existing_emails = {u.email for u in User.query.all()}
        users_to_add = [u for u in demo_users if u.email not in existing_emails]

        assets = [
            Asset(tag='AF-0012', name='Dell Laptop', category='Electronics', status='Allocated', location='Desk E12', allocated_to='Priya Shah', serial='SN-1001', condition='Good', is_shared=False),
            Asset(tag='AF-0021', name='Office Chair', category='Furniture', status='Available', location='Warehouse', serial='SN-2001', condition='Good', is_shared=True),
        ]
        existing_asset_tags = {a.tag for a in Asset.query.all()}
        assets_to_add = [a for a in assets if a.tag not in existing_asset_tags]

        departments = [
            Department(name='IT', head='Priya Shah', status='Active', parent_department='Operations'),
            Department(name='Operations', head='Rahul Verma', status='Active', parent_department=None),
        ]
        existing_department_names = {d.name for d in Department.query.all()}
        departments_to_add = [d for d in departments if d.name not in existing_department_names]

        categories = [
            AssetCategory(name='Electronics', description='Laptops, monitors and accessories', warranty_period='1 year'),
            AssetCategory(name='Furniture', description='Chairs, desks and office fixtures', warranty_period='6 months'),
        ]
        existing_category_names = {c.name for c in AssetCategory.query.all()}
        categories_to_add = [c for c in categories if c.name not in existing_category_names]

        if users_to_add or assets_to_add or departments_to_add or categories_to_add:
            try:
                db.session.add_all(users_to_add + assets_to_add + departments_to_add + categories_to_add)
                db.session.commit()
                print(f"✅ Demo data ensured. Added users={len(users_to_add)}, assets={len(assets_to_add)}, departments={len(departments_to_add)}, categories={len(categories_to_add)}")
            except Exception as exc:
                db.session.rollback()
                print(f"⚠️ Demo data seed hit a duplicate or conflict; continuing. {exc}")
        else:
            print("ℹ️ Demo data already present.")

    print("🚀 Starting AssetFlow...")
    app.run(debug=True, port=5000)
