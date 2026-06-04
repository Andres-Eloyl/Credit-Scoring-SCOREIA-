"""
SCOREIA — Tests del Módulo 3: Entrenamiento y Optimización
============================================================
Tests unitarios y de integración para SCOREIATrainer, SCOREIAEvaluator
y ModelSerializer.
"""

import json
import shutil
import sys
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest
import yaml
from sklearn.ensemble import RandomForestClassifier

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.module3_training.evaluator import SCOREIAEvaluator
from src.module3_training.model_serializer import ModelSerializer
from src.module3_training.trainer import SCOREIATrainer


# Clases Dummy para pruebas de serialización (pickleables)
class DummyCleaner:
    pass

class DummyEncoder:
    pass

class DummyRatios:
    pass

class DummySelector:
    pass


# ═══════════════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def temp_dirs(tmp_path):
    """Crea directorios temporales de prueba."""
    models_dir = tmp_path / "models"
    reports_dir = tmp_path / "reports"
    figures_dir = tmp_path / "reports" / "figures"
    
    models_dir.mkdir()
    figures_dir.mkdir(parents=True)
    
    return {
        "models": models_dir,
        "reports": reports_dir,
        "figures": figures_dir,
    }


@pytest.fixture
def sample_config():
    """Configuración simulada de SCOREIA."""
    return {
        "project": {
            "name": "SCOREIA-Test",
            "version": "0.1.0",
            "python_version": "3.14",
            "random_seed": 42,
        },
        "training": {
            "model": "RandomForestClassifier",
            "cv_folds": 2,
            "cv_scoring": "roc_auc",
            "n_iter_search": 2,
            "random_state": 42,
            "n_jobs": 1,
            "model_filename": "test_model.pkl",
            "metadata_filename": "test_metadata.json",
            "hyperparameter_space": {
                "n_estimators": [10, 20],
                "max_depth": [5, None],
            }
        },
        "metrics": {
            "target_auc_roc": 0.80,
            "target_f1_score": 0.72,
        },
        "paths": {
            "data_raw": "tests/test_data/",
            "models": "tests/test_models/",
            "reports": "tests/test_reports/",
        }
    }


# ═══════════════════════════════════════════════════════════════════════════
# TESTS: ModelSerializer
# ═══════════════════════════════════════════════════════════════════════════

class TestModelSerializer:
    """Tests para ModelSerializer."""

    def test_save_and_load_pipeline(self, temp_dirs):
        """Verifica que se guarda y carga el pipeline sin alteraciones."""
        serializer = ModelSerializer(models_dir=str(temp_dirs["models"]))
        
        # Instancias Dummy pickleables
        cleaner = DummyCleaner()
        encoder = DummyEncoder()
        ratios_gen = DummyRatios()
        selector = DummySelector()
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        
        feature_names = ["edad", "ingreso_mensual", "riesgo_compuesto"]

        # Guardar
        path = serializer.save_pipeline(
            cleaner=cleaner,
            encoder=encoder,
            ratios_generator=ratios_gen,
            selector=selector,
            model=model,
            feature_names=feature_names,
            filename="test_pipeline.pkl",
        )

        assert path.exists()
        assert path.name == "test_pipeline.pkl"

        # Cargar
        loaded = serializer.load_pipeline(filename="test_pipeline.pkl")
        
        assert "cleaner" in loaded
        assert "encoder" in loaded
        assert "ratios_generator" in loaded
        assert "selector" in loaded
        assert "model" in loaded
        assert loaded["feature_names"] == feature_names
        assert isinstance(loaded["model"], RandomForestClassifier)

    def test_save_metadata(self, temp_dirs, sample_config):
        """Verifica la correcta exportación de metadatos a JSON."""
        serializer = ModelSerializer(models_dir=str(temp_dirs["models"]))
        
        metrics = {
            "auc_roc": 0.85,
            "f1_score": 0.75,
            "precision": 0.73,
            "recall": 0.77,
            "accuracy": 0.80,
        }
        best_params = {"n_estimators": 50, "max_depth": 10}
        selected_features = ["f1", "f2", "f3"]

        path = serializer.save_metadata(
            metrics=metrics,
            best_params=best_params,
            selected_features=selected_features,
            config=sample_config,
            filename="test_metadata.json",
        )

        assert path.exists()
        
        # Leer JSON y validar estructura
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["project_name"] == "SCOREIA-Test"
        assert data["algorithm"] == "RandomForestClassifier"
        assert data["metrics"]["auc_roc"] == 0.85
        assert data["objectives_met"]["auc_roc"] is True
        assert data["objectives_met"]["f1_score"] is True
        assert data["objectives_met"]["all_met"] is True
        assert data["features"]["n_selected"] == 3
        assert data["features"]["selected_list"] == selected_features


# ═══════════════════════════════════════════════════════════════════════════
# TESTS: SCOREIAEvaluator
# ═══════════════════════════════════════════════════════════════════════════

class TestSCOREIAEvaluator:
    """Tests para SCOREIAEvaluator."""

    def test_evaluator_metrics_calculation(self, sample_config):
        """Verifica el cálculo correcto de métricas de rendimiento."""
        evaluator = SCOREIAEvaluator(config=sample_config)
        
        # Simular modelo y datos
        model = MagicMock()
        model.predict.return_value = np.array([0, 0, 1, 1, 0, 1])
        model.predict_proba.return_value = np.array([
            [0.9, 0.1],
            [0.8, 0.2],
            [0.3, 0.7],
            [0.2, 0.8],
            [0.7, 0.3],
            [0.1, 0.9],
        ])
        
        y_test = pd.Series([0, 0, 1, 0, 0, 1])
        X_test = pd.DataFrame({"feat1": range(6)})

        metrics = evaluator.evaluate(model, X_test, y_test)
        
        assert "auc_roc" in metrics
        assert "f1_score" in metrics
        assert "precision" in metrics
        assert "recall" in metrics
        assert "accuracy" in metrics
        
        # En este mock:
        # y_true = [0, 0, 1, 0, 0, 1]
        # y_pred = [0, 0, 1, 1, 0, 1]
        # TP = 2 (índices 2 y 5)
        # FP = 1 (índice 3)
        # TN = 3 (índices 0, 1, 4)
        # FN = 0
        assert metrics["true_positives"] == 2
        assert metrics["false_positives"] == 1
        assert metrics["true_negatives"] == 3
        assert metrics["false_negatives"] == 0
        
        # Accuracy: 5/6 = 0.8333
        assert pytest.approx(metrics["accuracy"], 0.01) == 0.8333
        # Recall: 2/2 = 1.0
        assert metrics["recall"] == 1.0
        # Precision: 2/3 = 0.6667
        assert pytest.approx(metrics["precision"], 0.01) == 0.6667

    def test_evaluator_plots_generation(self, sample_config, temp_dirs):
        """Verifica que se generen correctamente los archivos de gráficos."""
        evaluator = SCOREIAEvaluator(config=sample_config)
        
        model = MagicMock()
        model.predict.return_value = np.array([0, 0, 1, 1])
        model.predict_proba.return_value = np.array([
            [0.9, 0.1],
            [0.8, 0.2],
            [0.3, 0.7],
            [0.2, 0.8],
        ])
        
        y_test = pd.Series([0, 0, 1, 1])
        X_test = pd.DataFrame({"feat1": range(4)})

        # Ejecutar evaluación primero para llenar métricas
        evaluator.evaluate(model, X_test, y_test)
        
        # Graficar
        evaluator.plot_curves(model, X_test, y_test, output_dir=str(temp_dirs["figures"]))
        
        assert (temp_dirs["figures"] / "roc_curve.png").exists()
        assert (temp_dirs["figures"] / "precision_recall_curve.png").exists()
        assert (temp_dirs["figures"] / "confusion_matrix.png").exists()


# ═══════════════════════════════════════════════════════════════════════════
# TESTS: SCOREIATrainer (Integración Rápida)
# ═══════════════════════════════════════════════════════════════════════════

class TestSCOREIATrainer:
    """Tests para SCOREIATrainer."""

    def test_trainer_initialization(self, sample_config, tmp_path):
        """Verifica la correcta inicialización de los parámetros del Trainer."""
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(sample_config, f)
            
        trainer = SCOREIATrainer(config_path=str(config_file))
        
        assert trainer.random_seed == 42
        assert trainer.cv_folds == 2
        assert trainer.n_iter == 2
        assert trainer.n_jobs == 1
