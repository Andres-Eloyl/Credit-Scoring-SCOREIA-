"""
SCOREIA — Tests del Módulo 1: Preprocesamiento
=================================================
Tests unitarios para DataLoader, DataCleaner, FeatureEncoder,
ClassBalancer y PreprocessingPipeline.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Añadir el directorio raíz al path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.module1_preprocessing.data_loader import (
    DataLoader, EXPECTED_COLUMNS, LABEL_COLUMN,
    CATEGORICAL_COLUMNS, NUMERICAL_COLUMNS,
)
from src.module1_preprocessing.cleaner import DataCleaner
from src.module1_preprocessing.encoder import FeatureEncoder
from src.module1_preprocessing.balancer import ClassBalancer


# ═══════════════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def raw_data_path():
    """Ruta al dataset sintético generado."""
    path = ROOT_DIR / "data" / "raw" / "credit_data_synthetic.csv"
    if not path.exists():
        pytest.skip("Dataset sintetico no generado. Ejecute generate_synthetic_data.py")
    return str(path)


@pytest.fixture(scope="module")
def raw_df(raw_data_path):
    """Carga el dataset crudo."""
    return pd.read_csv(raw_data_path)


@pytest.fixture
def sample_df():
    """DataFrame sintético pequeño para tests rápidos."""
    np.random.seed(42)
    n = 200
    return pd.DataFrame({
        "edad":                np.random.randint(18, 76, n),
        "estado_civil":        np.random.choice(["Soltero", "Casado", "Divorciado", "Viudo"], n),
        "nivel_educativo":     np.random.choice(["Primaria", "Secundaria", "Universidad", "Posgrado"], n),
        "tipo_vivienda":       np.random.choice(["Propia", "Arrendada", "Familiar"], n),
        "ingreso_mensual":     np.random.uniform(800, 15000, n).round(2),
        "antiguedad_laboral":  np.random.randint(0, 361, n).astype(float),
        "tipo_contrato":       np.random.choice(["Indefinido", "Temporal", "Independiente"], n),
        "score_buro":          np.random.randint(300, 851, n).astype(float),
        "meses_mora_maxima":   np.random.randint(0, 13, n).astype(float),
        "num_creditos_activos": np.random.randint(0, 8, n),
        "consultas_buro_6m":   np.random.randint(0, 10, n).astype(float),
        "ratio_deuda_ingreso": np.random.uniform(0, 1.2, n).round(4),
        "utilizacion_credito": np.random.uniform(0, 1.0, n).round(4),
        "monto_solicitado":    np.random.uniform(500, 50000, n).round(2),
        "plazo_meses":         np.random.choice([6, 12, 18, 24, 36, 48, 60], n),
        "tipo_prestamo":       np.random.choice(["Personal", "Hipotecario", "Automotriz", "Tarjeta"], n),
        "incumplimiento":      np.random.choice([0, 0, 0, 0, 1], n),  # ~20%
    })


@pytest.fixture
def sample_df_with_nulls(sample_df):
    """DataFrame con valores nulos inyectados."""
    df = sample_df.copy()
    rng = np.random.default_rng(42)
    for col in ["score_buro", "meses_mora_maxima", "antiguedad_laboral"]:
        idx = rng.choice(len(df), size=10, replace=False)
        df.loc[idx, col] = np.nan
    return df


# ═══════════════════════════════════════════════════════════════════════════
# TESTS: DataLoader
# ═══════════════════════════════════════════════════════════════════════════

class TestDataLoader:
    """Tests para DataLoader."""

    def test_load_csv_success(self, raw_data_path):
        """Carga exitosa del dataset CSV."""
        loader = DataLoader(config_path="config.yaml")
        df = loader.load(raw_data_path, verbose=False)
        assert df is not None
        assert len(df) == 10_000

    def test_load_validates_schema(self, raw_data_path):
        """Verifica que el esquema se valida correctamente."""
        loader = DataLoader(config_path="config.yaml")
        df = loader.load(raw_data_path, validate=True, verbose=False)
        for col in EXPECTED_COLUMNS:
            assert col in df.columns

    def test_load_file_not_found(self):
        """Lanza FileNotFoundError si el archivo no existe."""
        loader = DataLoader()
        with pytest.raises(FileNotFoundError):
            loader.load("no_existe.csv")

    def test_quality_report_generated(self, raw_data_path):
        """El reporte de calidad se genera correctamente."""
        loader = DataLoader()
        loader.load(raw_data_path, verbose=False)
        report = loader.validation_report
        assert "n_rows" in report
        assert "total_nulls" in report
        assert "class_distribution" in report
        assert report["n_rows"] == 10_000


# ═══════════════════════════════════════════════════════════════════════════
# TESTS: DataCleaner
# ═══════════════════════════════════════════════════════════════════════════

class TestDataCleaner:
    """Tests para DataCleaner."""

    def test_imputation_fills_all_nulls(self, sample_df_with_nulls):
        """Tras limpieza, no deben quedar nulos en columnas imputables."""
        X = sample_df_with_nulls.drop(columns=["incumplimiento"])
        cleaner = DataCleaner()
        cleaner.fit(X)
        X_clean = cleaner.transform(X)
        assert X_clean[["score_buro", "meses_mora_maxima", "antiguedad_laboral"]].isnull().sum().sum() == 0

    def test_fit_learns_imputation_values(self, sample_df_with_nulls):
        """fit() debe aprender los valores de imputación."""
        X = sample_df_with_nulls.drop(columns=["incumplimiento"])
        cleaner = DataCleaner()
        cleaner.fit(X)
        assert "score_buro" in cleaner.impute_values_
        assert isinstance(cleaner.impute_values_["score_buro"], (float, np.floating))

    def test_capping_outliers(self, sample_df):
        """Los outliers deben quedar dentro de los límites IQR."""
        X = sample_df.drop(columns=["incumplimiento"]).copy()
        # Inyectar outlier extremo
        X.loc[0, "ingreso_mensual"] = 999_999.0
        cleaner = DataCleaner(iqr_multiplier=1.5)
        cleaner.fit(X)
        X_clean = cleaner.transform(X)
        upper = cleaner.iqr_bounds_["ingreso_mensual"]["upper"]
        assert X_clean["ingreso_mensual"].max() <= upper

    def test_no_data_leakage_separate_fit_transform(self, sample_df):
        """fit en un set y transform en otro no debe fallar."""
        X = sample_df.drop(columns=["incumplimiento"])
        X_train = X.iloc[:150]
        X_test = X.iloc[150:]
        cleaner = DataCleaner()
        cleaner.fit(X_train)
        X_test_clean = cleaner.transform(X_test)
        assert len(X_test_clean) == len(X_test)

    def test_cleaning_summary(self, sample_df_with_nulls):
        """get_cleaning_summary devuelve estructura correcta."""
        X = sample_df_with_nulls.drop(columns=["incumplimiento"])
        cleaner = DataCleaner()
        cleaner.fit(X)
        summary = cleaner.get_cleaning_summary()
        assert "imputation_rules" in summary
        assert "capping_rules" in summary


# ═══════════════════════════════════════════════════════════════════════════
# TESTS: FeatureEncoder
# ═══════════════════════════════════════════════════════════════════════════

class TestFeatureEncoder:
    """Tests para FeatureEncoder."""

    def test_ohe_removes_original_columns(self, sample_df):
        """OHE elimina las columnas categóricas originales."""
        X = sample_df.drop(columns=["incumplimiento"])
        encoder = FeatureEncoder()
        encoder.fit(X)
        X_enc = encoder.transform(X)
        for col in ["estado_civil", "tipo_vivienda", "tipo_contrato", "tipo_prestamo"]:
            assert col not in X_enc.columns

    def test_ohe_creates_dummy_columns(self, sample_df):
        """OHE crea las columnas dummy esperadas."""
        X = sample_df.drop(columns=["incumplimiento"])
        encoder = FeatureEncoder()
        encoder.fit(X)
        X_enc = encoder.transform(X)
        # Debe haber columnas como estado_civil_Soltero, etc.
        ohe_cols = [c for c in X_enc.columns if "estado_civil_" in c]
        assert len(ohe_cols) > 0

    def test_ordinal_encoding_nivel_educativo(self, sample_df):
        """nivel_educativo se codifica ordinalmente."""
        X = sample_df.drop(columns=["incumplimiento"])
        encoder = FeatureEncoder()
        encoder.fit(X)
        X_enc = encoder.transform(X)
        assert "nivel_educativo" in X_enc.columns
        assert set(X_enc["nivel_educativo"].unique()).issubset({0, 1, 2, 3})

    def test_more_features_after_encoding(self, sample_df):
        """El número de features aumenta tras OHE."""
        X = sample_df.drop(columns=["incumplimiento"])
        encoder = FeatureEncoder()
        encoder.fit(X)
        X_enc = encoder.transform(X)
        assert X_enc.shape[1] > X.shape[1]

    def test_ohe_values_are_binary(self, sample_df):
        """Todas las columnas dummy deben ser 0 o 1."""
        X = sample_df.drop(columns=["incumplimiento"])
        encoder = FeatureEncoder()
        encoder.fit(X)
        X_enc = encoder.transform(X)
        ohe_cols = [c for c in X_enc.columns if "_" in c and c.split("_")[0] in
                    ["estado", "tipo"]]
        for col in ohe_cols:
            assert set(X_enc[col].unique()).issubset({0, 1}), f"{col} no es binario"


# ═══════════════════════════════════════════════════════════════════════════
# TESTS: ClassBalancer
# ═══════════════════════════════════════════════════════════════════════════

class TestClassBalancer:
    """Tests para ClassBalancer."""

    def test_smote_balances_classes(self, sample_df):
        """SMOTE debe equilibrar las clases."""
        X = sample_df.drop(columns=["incumplimiento"])
        # Codificar para que sea numérico
        encoder = FeatureEncoder()
        cleaner = DataCleaner()
        cleaner.fit(X)
        X_clean = cleaner.transform(X)
        encoder.fit(X_clean)
        X_enc = encoder.transform(X_clean)
        y = sample_df["incumplimiento"]

        balancer = ClassBalancer(method="smote", random_state=42)
        X_bal, y_bal = balancer.fit_resample(X_enc, y)

        # Tras SMOTE, ambas clases deben tener la misma cantidad
        assert y_bal.value_counts()[0] == y_bal.value_counts()[1]

    def test_smote_increases_samples(self, sample_df):
        """SMOTE debe generar más muestras que el dataset original."""
        X = sample_df.drop(columns=["incumplimiento"])
        encoder = FeatureEncoder()
        cleaner = DataCleaner()
        cleaner.fit(X)
        X_clean = cleaner.transform(X)
        encoder.fit(X_clean)
        X_enc = encoder.transform(X_clean)
        y = sample_df["incumplimiento"]

        balancer = ClassBalancer(method="smote", random_state=42)
        X_bal, y_bal = balancer.fit_resample(X_enc, y)
        assert len(y_bal) > len(y)

    def test_smote_rejects_categorical_data(self, sample_df):
        """SMOTE debe rechazar datos con columnas categóricas."""
        X = sample_df.drop(columns=["incumplimiento"])
        y = sample_df["incumplimiento"]
        balancer = ClassBalancer()
        with pytest.raises(ValueError, match="numericos"):
            balancer.fit_resample(X, y)

    def test_invalid_method_raises(self):
        """Método inválido lanza ValueError."""
        with pytest.raises(ValueError, match="no soportado"):
            ClassBalancer(method="invalid_method")

    def test_balancing_summary(self, sample_df):
        """get_balancing_summary retorna estructura correcta."""
        X = sample_df.drop(columns=["incumplimiento"])
        encoder = FeatureEncoder()
        cleaner = DataCleaner()
        cleaner.fit(X)
        X_clean = cleaner.transform(X)
        encoder.fit(X_clean)
        X_enc = encoder.transform(X_clean)
        y = sample_df["incumplimiento"]

        balancer = ClassBalancer(method="smote", random_state=42)
        balancer.fit_resample(X_enc, y)
        summary = balancer.get_balancing_summary()
        assert "before" in summary
        assert "after" in summary
        assert "n_synthetic" in summary
        assert summary["n_synthetic"] > 0
