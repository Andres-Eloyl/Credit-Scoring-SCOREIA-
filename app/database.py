import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

# Cargar variables de entorno desde .env si existe
load_dotenv()

# Ruta absoluta al directorio data (para fallback local)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Buscar URL de Supabase en .env, si no existe, usar SQLite
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Supabase (PostgreSQL)
    SQLALCHEMY_DATABASE_URL = DATABASE_URL
    # Connect args for Postgres shouldn't include check_same_thread
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
else:
    # Fallback SQLite
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{os.path.join(DATA_DIR, 'scoreia.db')}"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependencia para FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
