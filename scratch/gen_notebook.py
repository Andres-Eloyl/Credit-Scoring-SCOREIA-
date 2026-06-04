import nbformat as nbf
import os

nb = nbf.v4.new_notebook()
text = """\
# SCOREIA - Módulo 5: Monitoreo y Auditoría (Demo)
Este notebook demuestra cómo utilizar las clases de monitoreo para detectar Data Drift, generar un Dashboard interactivo y auditar la equidad del modelo."""

code1 = """\
import pandas as pd
import numpy as np
from src.module5_monitoring.drift_detector import DriftDetector
from src.module5_monitoring.fairness_audit import FairnessAudit
from src.module5_monitoring.dashboard import MonitoringDashboard

# Cargamos un poco de datos crudos (simulando producción vs entrenamiento)
df = pd.read_csv("data/raw/credit_data_synthetic.csv")

# Dividimos el dataset para simular Referencia vs Actual
# (En un caso real, Reference es Train, Actual es la data de este mes)
ref_df = df.iloc[:5000].copy()
curr_df = df.iloc[5000:7000].copy()

# Para simular Drift, vamos a alterar los ingresos y el score_buro en la data actual
curr_df['ingreso_mensual'] = curr_df['ingreso_mensual'] * 0.7
curr_df['score_buro'] = curr_df['score_buro'] - 100
"""

text2 = """\
## 1. Detección de Data Drift
Generamos el reporte de Data Drift con Evidently."""

code2 = """\
detector = DriftDetector("config.yaml")
is_drifting = detector.generate_report(ref_df, curr_df, filename="demo_drift.html")
print(f"¿Hay Drift general?: {is_drifting}")
"""

text3 = """\
## 2. Auditoría de Equidad (Fairness)
Para la equidad necesitamos la predicción real de nuestro modelo vs el target real."""

code3 = """\
from src.module4_inference.predictor import Predictor

# Cargamos el predictor
predictor = Predictor("models/scoreia_rf_v1.pkl", "config.yaml")

# Hacemos inferencia sobre los primeros 1000 registros para ser rápidos
eval_df = df.iloc[:1000].copy()
# Target es "incumplimiento"
if "incumplimiento" in eval_df.columns:
    target_col = "incumplimiento"
else:
    target_col = "Incumplimiento" # Revisa el nombre exacto

predictions = predictor.predict(eval_df)

# Juntamos target y predicción
eval_df["pred_class"] = (predictions["pd"] >= 0.5).astype(int)

auditor = FairnessAudit("config.yaml")
fairness_results = auditor.audit(eval_df, target_col="incumplimiento", pred_col="pred_class")

import json
print(json.dumps(fairness_results, indent=2))
"""

text4 = """\
## 3. Dashboard Interactivo de Evidently
Genera un reporte HTML completo (Calidad de datos, Drift, Rendimiento)."""

code4 = """\
dashboard_gen = MonitoringDashboard("config.yaml")
# Preparamos las columnas
ref_dash = eval_df.iloc[:500].copy()
curr_dash = eval_df.iloc[500:1000].copy()

dashboard_gen.generate_dashboard(
    ref_df=ref_dash, 
    curr_df=curr_dash, 
    target_col="incumplimiento", 
    pred_col="pred_class", 
    filename="demo_dashboard.html"
)
print("Dashboard generado en reports/monitoring/demo_dashboard.html")
"""

nb['cells'] = [
    nbf.v4.new_markdown_cell(text),
    nbf.v4.new_code_cell(code1),
    nbf.v4.new_markdown_cell(text2),
    nbf.v4.new_code_cell(code2),
    nbf.v4.new_markdown_cell(text3),
    nbf.v4.new_code_cell(code3),
    nbf.v4.new_markdown_cell(text4),
    nbf.v4.new_code_cell(code4)
]

os.makedirs("notebooks", exist_ok=True)
with open("notebooks/05_monitoring_demo.ipynb", "w", encoding="utf-8") as f:
    nbf.write(nb, f)
