from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from .database import Base

class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Inputs
    client_id = Column(String, index=True)
    edad = Column(Integer)
    ingreso_mensual = Column(Float)
    score_buro = Column(Integer)
    monto_solicitado = Column(Float)
    plazo_meses = Column(Integer)
    
    # Outputs
    pd_value = Column(Float)
    riesgo = Column(String)
    decision = Column(String)
