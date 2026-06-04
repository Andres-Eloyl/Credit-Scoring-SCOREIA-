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
def predict_credit(req: CreditRequest):
    if not predictor:
        raise HTTPException(status_code=500, detail="El modelo no está disponible.")
        
    data_dict = req.model_dump()
    client_id = data_dict.pop("client_id")
    
    # Realizar predicción
    try:
        prediction_df = predictor.predict(data_dict)
        pd_val = float(prediction_df.iloc[0]["pd"])
        
        # Segmentación
        segment_df = segmentor.segment(prediction_df)
        riesgo = segment_df.iloc[0]["riesgo"]
        
        # Explicabilidad: Guardar gráfico SHAP
        explainer.explain_individual(data_dict, client_id)
        
        # Leer el gráfico SHAP generado y codificarlo en Base64
        shap_path = Path(f"reports/decisions/shap_waterfall_{client_id}.png")
        shap_base64 = ""
        if shap_path.exists():
            with open(shap_path, "rb") as image_file:
                shap_base64 = base64.b64encode(image_file.read()).decode('utf-8')
                
        return {
            "client_id": client_id,
            "pd": pd_val,
            "riesgo": riesgo,
            "decision": "Aprobado" if pd_val < 0.60 else "Rechazado",
            "shap_image_b64": shap_base64
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Montar los archivos estáticos de la UI generada
ui_dir = Path(__file__).parent / "ui"
if not ui_dir.exists():
    ui_dir.mkdir(parents=True, exist_ok=True)

app.mount("/", StaticFiles(directory=str(ui_dir), html=True), name="ui")

if __name__ == "__main__":
    import uvicorn
    # Se debe correr desde la raíz: python -m app.main_api
    uvicorn.run("app.main_api:app", host="0.0.0.0", port=8000, reload=True)
