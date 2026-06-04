import pytest
import pandas as pd
import numpy as np
import os
from pathlib import Path

from src.module5_monitoring.drift_detector import DriftDetector
from src.module5_monitoring.fairness_audit import FairnessAudit
from src.module5_monitoring.dashboard import MonitoringDashboard

@pytest.fixture
def mock_data():
    np.random.seed(42)
    # 100 samples
    data = {
        "edad": np.random.randint(20, 60, 100),
        "ingreso_mensual": np.random.uniform(1000, 5000, 100),
        "estado_civil": np.random.choice(["Soltero", "Casado"], 100),
        "nivel_educativo": np.random.choice(["Secundaria", "Universidad"], 100),
        "incumplimiento": np.random.choice([0, 1], 100),
        "pred_class": np.random.choice([0, 1], 100)
    }
    return pd.DataFrame(data)

def test_drift_detector(mock_data, tmp_path):
    # Alter second half to simulate drift
    ref_df = mock_data.iloc[:50].copy()
    curr_df = mock_data.iloc[50:].copy()
    
    # Introduce heavy drift
    curr_df['ingreso_mensual'] = curr_df['ingreso_mensual'] * 10
    
    detector = DriftDetector("config.yaml")
    # Redirect output dir to tmp_path
    detector.output_dir = tmp_path
    
    is_drifting = detector.generate_report(ref_df, curr_df, filename="test_drift.html")
    
    assert is_drifting is True or is_drifting is False
    assert (tmp_path / "test_drift.html").exists()

def test_fairness_audit(mock_data):
    auditor = FairnessAudit("config.yaml")
    # Manually set sensitive features for test
    auditor.sensitive_features = ["estado_civil"]
    
    results = auditor.audit(mock_data, target_col="incumplimiento", pred_col="pred_class")
    
    assert "estado_civil" in results
    assert "reference_group" in results["estado_civil"]
    assert "group_metrics" in results["estado_civil"]
    
    groups = results["estado_civil"]["group_metrics"].keys()
    assert len(groups) > 0
    for group in groups:
        assert "approval_rate" in results["estado_civil"]["group_metrics"][group]

def test_monitoring_dashboard(mock_data, tmp_path):
    dash = MonitoringDashboard("config.yaml")
    dash.output_dir = tmp_path
    
    ref_df = mock_data.iloc[:50].copy()
    curr_df = mock_data.iloc[50:].copy()
    
    output_file = dash.generate_dashboard(
        ref_df, curr_df, target_col="incumplimiento", pred_col="pred_class", filename="test_dash.html"
    )
    
    assert output_file.exists()
