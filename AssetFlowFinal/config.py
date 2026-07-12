import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
DB_PATH = os.path.join(INSTANCE_DIR, "assetflow.db")

# Ensure the sqlite folder exists; otherwise SQLAlchemy/SQLite fails with:
# "unable to open database file".
os.makedirs(INSTANCE_DIR, exist_ok=True)

class Config:
    SECRET_KEY = 'assetflow-hackathon-2026-secret'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Change this to MySQL when ready:
    # SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://assetflow_user:password123@localhost/assetflow'
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DB_PATH}"  # Easy for hackathon
