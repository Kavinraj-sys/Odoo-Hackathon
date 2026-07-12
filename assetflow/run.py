from app import app, db
from models import User, Asset, Department

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        print("Seeding/ensuring demo data...")

        # Create-only: do not overwrite existing users/passwords.
        # This ensures demo accounts work even if the DB already contains some users.
        demo_users = [
            User(email='admin@company.com', password='password', name='Admin User', role='Admin'),
            User(email='priya@company.com', password='password', name='Priya Shah', role='AssetManager'),
            User(email='rahul@company.com', password='password', name='Rahul Verma', role='DepartmentHead'),
            # Correct email kept:
            User(email='john@company.com', password='password', name='John Doe', role='Employee'),
            # Also add the exact typo requested to make login work:
            User(email='john@comapny.com', password='password', name='John Doe (typo email)', role='Employee'),
        ]

        existing_emails = {u.email for u in User.query.all()}
        users_to_add = [u for u in demo_users if u.email not in existing_emails]

        assets = [
            Asset(tag='AF-0012', name='Dell Laptop', category='Electronics', status='Allocated', location='Desk E12', allocated_to='Priya Shah'),
            Asset(tag='AF-0021', name='Office Chair', category='Furniture', status='Available', location='Warehouse'),
        ]
        existing_asset_tags = {a.tag for a in Asset.query.all()}
        assets_to_add = [a for a in assets if a.tag not in existing_asset_tags]

        if users_to_add or assets_to_add:
            db.session.add_all(users_to_add + assets_to_add)
            db.session.commit()
            print(f"✅ Demo data ensured. Added users={len(users_to_add)}, assets={len(assets_to_add)}")
        else:
            print("ℹ️ Demo data already present.")

    print("🚀 Starting AssetFlow...")
    app.run(debug=True, port=5000)
