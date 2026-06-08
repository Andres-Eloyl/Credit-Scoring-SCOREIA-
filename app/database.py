import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:

    SQLALCHEMY_DATABASE_URL = DATABASE_URL

    engine = create_engine(SQLALCHEMY_DATABASE_URL)
else:

    SQLALCHEMY_DATABASE_URL = f"sqlite:///{os.path.join(DATA_DIR, 'scoreia.db')}"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
