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

@app.get("/api/status")
def read_root():
    return {"status": "ok", "model_loaded": predictor is not None}

@app.post("/api/predict")
async def predict(data: dict, db: Session = Depends(database.get_db)):
    if not predictor:
        raise HTTPException(status_code=500, detail="El modelo no está disponible.")
    
    # Extraer client_id y quitarlo de features
    client_id = data.get("client_id", "Unknown")
    data_dict = data.copy()
    data_dict.pop("client_id", None)
    
    # Realizar predicción
    try:
        prediction_df = predictor.predict(data_dict)
        pd_val = float(prediction_df.iloc[0]["pd"])
        
        # Segmentación
        riesgo = prediction_df.iloc[0]["risk_segment"]
        
        # Explicabilidad: Extraer datos crudos para dashboard interactivo
        shap_data = explainer.get_shap_values_dict(data_dict)
        decision_text = "Aprobado" if pd_val < 0.60 else "Rechazado"

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

# Montar los archivos estáticos de la UI generada
ui_dir = Path(__file__).parent / "ui"
if not ui_dir.exists():
    ui_dir.mkdir(parents=True, exist_ok=True)

app.mount("/", StaticFiles(directory=str(ui_dir), html=True), name="ui")

if __name__ == "__main__":
    import uvicorn
    # Se debe correr desde la raíz: python -m app.main_api
    uvicorn.run("app.main_api:app", host="0.0.0.0", port=8000, reload=True)
