import json
from src.module4_inference.predictor import Predictor
import pandas as pd
import traceback

data = {
    "edad": 35,
    "estado_civil": "",
    "nivel_educativo": "",
    "tipo_vivienda": "",
    "ingreso_mensual": 4500.0,
    "antiguedad_laboral": 60,
    "tipo_contrato": "",
    "score_buro": 720,
    "tipo_prestamo": "",
    "monto_solicitado": 15000.0,
    "plazo_meses": 36,
    "meses_mora_maxima": 0,
    "num_creditos_activos": 2,
    "consultas_buro_6m": 1,
    "ratio_deuda_ingreso": 0.30,
    "utilizacion_credito": 0.45
}

predictor = Predictor(model_path="models/scoreia_rf_v1.pkl", config_path="config.yaml")
try:
    df = pd.DataFrame([data])
    print("Dtypes before preprocess:")
    print(df.dtypes)
    
    # Run cleaner
    X_clean = predictor.cleaner.transform(df)
    print("Dtypes after cleaner:")
    print(X_clean.dtypes)
    
    # Run encoder
    X_enc = predictor.encoder.transform(X_clean)
    print("Dtypes after encoder:")
    print(X_enc.dtypes)
    
    # Run ratios
    X_ratios = predictor.ratios_generator.transform(X_enc)
    print("Dtypes after ratios:")
    print(X_ratios.dtypes)
    
    # Run selector (WoE is usually inside selector?)
    # Wait, WoE is where? Is it predictor.selector?
    # Let's check type of selector
    print("Type of selector:", type(predictor.selector))
    X_sel = predictor.selector.transform(X_ratios)
    
    df_pred = predictor.predict(data)
    print("Success:", df_pred)
except Exception as e:
    traceback.print_exc()
