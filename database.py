import os
import ssl
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool

# Detect if running on Render (production)
IS_PRODUCTION = os.environ.get("RENDER") is not None

if IS_PRODUCTION:
    # --- PRODUCTION (CANLI): Supabase PostgreSQL ---
    # Sadece Render'dayken gercek kullanici verilerine baglanir.
    db_url = "postgresql+pg8000://postgres.otvuhuyoonypyrqlszhz:frknbyrmM.58@aws-1-eu-west-1.pooler.supabase.com:5432/postgres"
    
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    engine = create_engine(
        db_url,
        connect_args={"ssl_context": ssl_context},
        poolclass=NullPool
    )
else:
    # --- LOCAL DEVELOPMENT (TEST): SQLite ---
    # Kendi bilgisayarinda test yaparken bu sahte veritabanini kullanir, 
    # boylece canlidaki kullanici verileri ASLA bozulmaz.
    engine = create_engine(
        "sqlite:///./broker.db", connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        return True
    except Exception as e:
        print(f"DB init error: {e}")
        return False

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
