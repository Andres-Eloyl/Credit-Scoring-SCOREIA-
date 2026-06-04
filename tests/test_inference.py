import os
import pandas as pd
import pytest
import shap
from pathlib import Path

from src.module4_inference.risk_segmentor import RiskSegmentor
from src.module4_inference.predictor import Predictor
from src.module4_inference.explainability import ModelExplainer

@pytest.fixture
def sample_data():
    return {
        "edad": 35,
        "estado_civil": "Casado",
        "nivel_educativo": "Universidad",
        "tipo_vivienda": "Propia",
        "ingreso_mensual": 4500.0,
        "antiguedad_laboral": 48,
        "tipo_contrato": "Indefinido",
        "score_buro": 680,
        "meses_mora_maxima": 0,
        "num_creditos_activos": 2,
        "consultas_buro_6m": 1,
        "ratio_deuda_ingreso": 0.35,
        "utilizacion_credito": 0.40,
        "monto_solicitado": 15000.0,
        "plazo_meses": 36,
        "tipo_prestamo": "Personal"
    }

def test_risk_segmentor():
    segmentor = RiskSegmentor("config.yaml")
    
    assert segmentor.segment(0.15) == "Bajo"
    assert segmentor.segment(0.29) == "Bajo"
    assert segmentor.segment(0.30) == "Medio"
    assert segmentor.segment(0.55) == "Medio"
    assert segmentor.segment(0.60) == "Alto"
    assert segmentor.segment(0.95) == "Alto"

def test_predictor_single_record(sample_data):
    predictor = Predictor("models/scoreia_rf_v1.pkl", "config.yaml")
    result = predictor.predict(sample_data)
    
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 1
    assert "pd" in result.columns
    assert "risk_segment" in result.columns
    
    pd_value = result["pd"].iloc[0]
    assert 0.0 <= pd_value <= 1.0
    assert result["risk_segment"].iloc[0] in ["Bajo", "Medio", "Alto"]

def test_predictor_batch_records(sample_data):
    batch_data = [sample_data, sample_data.copy()]
    batch_data[1]["score_buro"] = 300 # Peor score
    batch_data[1]["meses_mora_maxima"] = 12
    
    predictor = Predictor("models/scoreia_rf_v1.pkl", "config.yaml")
    result = predictor.predict(batch_data)
    
    assert len(result) == 2
    assert "pd" in result.columns
    assert "risk_segment" in result.columns
    
    # El segundo registro debería tener mayor PD por el peor score
    assert result["pd"].iloc[1] > result["pd"].iloc[0]

def test_explainability(sample_data, tmp_path):
    predictor = Predictor("models/scoreia_rf_v1.pkl", "config.yaml")
    explainer = ModelExplainer(predictor, output_dir=str(tmp_path))
    
    # Test individual explanation
    explainer.explain_individual(sample_data, client_id="test_001")
    
    expected_waterfall_path = tmp_path / "shap_waterfall_test_001.png"
    assert expected_waterfall_path.exists()
    
    # Test global explanation
    batch_data = [sample_data, sample_data.copy()]
    batch_data[1]["score_buro"] = 300
    df_batch = pd.DataFrame(batch_data)
    
    explainer.explain_global(df_batch, filename="test_summary.png")
    expected_summary_path = Path("reports/figures/test_summary.png")
    assert expected_summary_path.exists()
    
    # Cleanup summary plot as it is saved outside tmp_path
    if expected_summary_path.exists():
        expected_summary_path.unlink()
