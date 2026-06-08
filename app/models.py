from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from .database import Base

class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    client_name = Column(String, index=True)
    client_id = Column(String, index=True)
    
    monto_solicitado = Column(Float)
    plazo_meses = Column(Integer)
    pd_value = Column(Float)
    riesgo = Column(String)
    decision = Column(String)
    
    request_data = Column(String)
    shap_data = Column(String)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    role = Column(String)
    department = Column(String)
    phone = Column(String)
    country = Column(String)
    state = Column(String)
    city = Column(String)
    address = Column(String)
    password_hash = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class PasswordReset(Base):
    __tablename__ = "password_resets"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True)
    token = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
