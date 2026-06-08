from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import pandas as pd
import os
import base64
from pathlib import Path

from src.module4_inference.predictor import Predictor
from src.module4_inference.risk_segmentor import RiskSegmentor
from src.module4_inference.explainability import ModelExplainer

import uuid
from datetime import datetime, timedelta
import bcrypt
from app.email_service import send_recovery_email

def hash_password(password: str) -> str:
    pwd_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    pwd_bytes = plain_password.encode('utf-8')[:72]
    hash_bytes = hashed_password.encode('utf-8')
    try:
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception:
        return False

from fastapi import Depends
from sqlalchemy.orm import Session
from app import models, database

# Crear las tablas en la BD
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="SCOREIA API", description="API para el modelo de Credit Scoring", version="1.0.0")

# Permitir CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar modelo y clases de inferencia (globales)
try:
    predictor = Predictor(model_path="models/scoreia_rf_v1.pkl", config_path="config.yaml")
    segmentor = RiskSegmentor(config_path="config.yaml")
    explainer = ModelExplainer(predictor=predictor, output_dir="reports/decisions")
except Exception as e:
    print(f"Error cargando el modelo: {e}")
    predictor = None
    segmentor = None
    explainer = None

class CreditRequest(BaseModel):
    client_id: str
    edad: int
    estado_civil: str
    nivel_educativo: str
    tipo_vivienda: str
    ingreso_mensual: float
    antiguedad_laboral: int
    tipo_contrato: str
    score_buro: int
    meses_mora_maxima: int
    num_creditos_activos: int
    consultas_buro_6m: int
    ratio_deuda_ingreso: float
    utilizacion_credito: float
    monto_solicitado: float
    plazo_meses: int
    tipo_prestamo: str

class UserRegister(BaseModel):
    name: str
    email: str
    password: str
    role: str
    department: str
    phone: str
    country: str
    state: str
    city: str
    address: str

class UserLogin(BaseModel):
    email: str
    password: str

class ForgotPassword(BaseModel):
    email: str

class ResetPassword(BaseModel):
    token: str
    new_password: str

@app.post("/api/auth/register")
async def register(data: UserRegister, db: Session = Depends(database.get_db)):
    if db.query(models.User).filter(models.User.email == data.email).first():
        raise HTTPException(status_code=400, detail="El correo ya está registrado.")
    
    hashed_pwd = hash_password(data.password)
    user = models.User(
        name=data.name,
        email=data.email,
        password_hash=hashed_pwd,
        role=data.role,
        department=data.department,
        phone=data.phone,
        country=data.country,
        state=data.state,
        city=data.city,
        address=data.address
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"status": "success", "message": "Usuario registrado exitosamente."}

@app.post("/api/auth/login")
async def login(data: UserLogin, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == data.email).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Credenciales inválidas.")
    
    return {
        "status": "success",
        "user": {
            "name": user.name,
            "email": user.email,
            "role": user.role
        }
    }

@app.post("/api/auth/forgot-password")
async def forgot_password(data: ForgotPassword, request: Request, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == data.email).first()
    if not user:
        return {"status": "success"} # Prevent email enumeration
    
    token = str(uuid.uuid4())
    expires = datetime.utcnow() + timedelta(hours=1)
    
    reset_record = models.PasswordReset(email=user.email, token=token, expires_at=expires)
    db.add(reset_record)
    db.commit()
    
    base_url = str(request.base_url).rstrip("/")
    send_recovery_email(user.email, token, base_url)
    
    return {"status": "success"}

@app.post("/api/auth/reset-password")
async def reset_password(data: ResetPassword, db: Session = Depends(database.get_db)):
    record = db.query(models.PasswordReset).filter(
        models.PasswordReset.token == data.token,
        models.PasswordReset.expires_at > datetime.utcnow()
    ).first()
    
    if not record:
        raise HTTPException(status_code=400, detail="Token inválido o expirado.")
    
    user = db.query(models.User).filter(models.User.email == record.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
        
    user.password_hash = hash_password(data.new_password)
    db.delete(record)
    db.commit()
    return {"status": "success", "message": "Contraseña actualizada exitosamente."}

@app.get("/api/status")
def read_root():
    return {"status": "ok", "model_loaded": predictor is not None}

@app.post("/api/predict")
async def predict(data: dict, db: Session = Depends(database.get_db)):
    if not predictor:
        raise HTTPException(status_code=500, detail="El modelo no está disponible.")
    
    # Extraer client_id y risk_threshold
    client_id = data.get("client_id", "Unknown")
    risk_threshold = float(data.get("risk_threshold", 0.60))
    
    data_dict = data.copy()
    data_dict.pop("client_id", None)
    data_dict.pop("risk_threshold", None)
    
    # Realizar predicción
    try:
        prediction_df = predictor.predict(data_dict)
        pd_val = float(prediction_df.iloc[0]["pd"])
        
        # Segmentación
        riesgo = prediction_df.iloc[0]["risk_segment"]
        
        # Explicabilidad: Extraer datos crudos para dashboard interactivo
        shap_data = explainer.get_shap_values_dict(data_dict)
        decision_text = "Aprobado" if pd_val <= risk_threshold else "Rechazado"

        # Guardar en base de datos
        db_eval = models.Evaluation(
            client_id=client_id,
            edad=data.get("edad"),
            ingreso_mensual=data.get("ingreso_mensual"),
            score_buro=data.get("score_buro"),
            monto_solicitado=data.get("monto_solicitado"),
            plazo_meses=data.get("plazo_meses"),
            pd_value=pd_val,
            riesgo=riesgo,
            decision=decision_text
        )
        db.add(db_eval)
        db.commit()
        db.refresh(db_eval)

        return {
            "status": "success",
            "client_id": client_id,
            "pd": pd_val,
            "riesgo": riesgo,
            "decision": decision_text,
            "shap_data": shap_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/history")
async def get_history(limit: int = 10, db: Session = Depends(database.get_db)):
    evals = db.query(models.Evaluation).order_by(models.Evaluation.timestamp.desc()).limit(limit).all()
    return evals

from sqlalchemy import func

@app.get("/api/stats")
async def get_stats(db: Session = Depends(database.get_db)):
    # Total evaluaciones
    total = db.query(models.Evaluation).count()
    if total == 0:
        return {"total": 0, "aprobados": 0, "rechazados": 0, "monto_total": 0, "pd_promedio": 0, "history_dates": [], "history_aprobados": [], "history_rechazados": []}
    
    # Aprobados vs Rechazados
    aprobados = db.query(models.Evaluation).filter(models.Evaluation.decision == "Aprobado").count()
    rechazados = total - aprobados
    
    # Monto total
    monto_total = db.query(func.sum(models.Evaluation.monto_solicitado)).scalar() or 0
    
    # PD promedio
    pd_promedio = db.query(func.avg(models.Evaluation.pd_value)).scalar() or 0

    return {
        "total": total,
        "aprobados": aprobados,
        "rechazados": rechazados,
        "monto_total": monto_total,
        "pd_promedio": pd_promedio
    }

ui_dir = Path(__file__).parent / "ui"
if not ui_dir.exists():
    ui_dir.mkdir(parents=True, exist_ok=True)

@app.get("/")
async def root_view():
    return FileResponse(ui_dir / "index.html")

@app.get("/login")
async def login_view():
    return FileResponse(ui_dir / "login.html")

@app.get("/reset-password")
async def reset_password_view():
    return FileResponse(ui_dir / "reset_password.html")

@app.get("/app")
async def app_view():
    return FileResponse(ui_dir / "app.html")

@app.get("/funcionalidades")
async def features_view():
    return FileResponse(ui_dir / "features.html")

@app.get("/teoria")
async def theory_view():
    return FileResponse(ui_dir / "theory.html")

@app.get("/tecnologia")
async def tech_view():
    return FileResponse(ui_dir / "tech.html")

@app.get("/soporte")
async def support_view():
    return FileResponse(ui_dir / "support.html")

@app.get("/casos-de-uso")
async def use_cases_view():
    return FileResponse(ui_dir / "use_cases.html")

@app.get("/acerca-de")
async def about_view():
    return FileResponse(ui_dir / "about.html")

app.mount("/", StaticFiles(directory=str(ui_dir), html=False), name="ui")

if __name__ == "__main__":
    import uvicorn
    # Se debe correr desde la raíz: python -m app.main_api
    uvicorn.run("app.main_api:app", host="0.0.0.0", port=8000, reload=True)
