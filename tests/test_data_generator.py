"""
tests/test_data_generator.py
============================
Tests unitarios para el generador de dataset sintético.
Verifican que el dataset cumple con las especificaciones de SCOREIA.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Añadir el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.generate_synthetic_data import generate_dataset


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def sample_dataset(tmp_path_factory):
    """Genera un dataset pequeño para pruebas (500 registros)."""
    tmp = tmp_path_factory.mktemp("data")
    df = generate_dataset(
        n_samples=500,
        target_default_rate=0.20,
        missing_rate=0.02,
        output_dir=str(tmp),
        output_filename="test_dataset.csv",
        random_seed=42,
    )
    return df


# ─── Tests de Estructura ─────────────────────────────────────────────────────

class TestDatasetStructure:
    """Tests que verifican la estructura y columnas del dataset."""

    EXPECTED_COLUMNS = [
        "edad", "estado_civil", "nivel_educativo", "tipo_vivienda",
        "ingreso_mensual", "antiguedad_laboral", "tipo_contrato",
        "score_buro", "meses_mora_maxima", "num_creditos_activos",
        "consultas_buro_6m", "ratio_deuda_ingreso", "utilizacion_credito",
        "monto_solicitado", "plazo_meses", "tipo_prestamo", "incumplimiento",
    ]

    def test_column_count(self, sample_dataset):
        """El dataset debe tener exactamente 17 columnas (16 features + 1 label)."""
        assert len(sample_dataset.columns) == 17

    def test_column_names_exact(self, sample_dataset):
        """Los nombres de columnas deben coincidir exactamente con el diseño."""
        assert list(sample_dataset.columns) == self.EXPECTED_COLUMNS

    def test_row_count(self, sample_dataset):
        """El dataset debe tener exactamente 500 registros (n_samples)."""
        assert len(sample_dataset) == 500


# ─── Tests de Tipos de Datos ─────────────────────────────────────────────────

class TestDataTypes:
    """Tests que verifican los tipos de datos de cada columna."""

    def test_edad_is_integer(self, sample_dataset):
        assert pd.api.types.is_integer_dtype(sample_dataset["edad"])

    def test_ingreso_mensual_is_float(self, sample_dataset):
        assert pd.api.types.is_float_dtype(sample_dataset["ingreso_mensual"])

    def test_estado_civil_is_string(self, sample_dataset):
        dtype = sample_dataset["estado_civil"].dtype
        assert pd.api.types.is_object_dtype(dtype) or pd.api.types.is_string_dtype(dtype)

    def test_incumplimiento_is_binary(self, sample_dataset):
        assert set(sample_dataset["incumplimiento"].unique()).issubset({0, 1})


# ─── Tests de Rangos de Valores ───────────────────────────────────────────────

class TestValueRanges:
    """Tests que verifican que los valores están dentro de rangos esperados."""

    def test_edad_range(self, sample_dataset):
        assert sample_dataset["edad"].min() >= 18
        assert sample_dataset["edad"].max() <= 75

    def test_score_buro_range(self, sample_dataset):
        valid = sample_dataset["score_buro"].dropna()
        assert valid.min() >= 300
        assert valid.max() <= 850

    def test_utilizacion_credito_range(self, sample_dataset):
        valid = sample_dataset["utilizacion_credito"].dropna()
        assert valid.min() >= 0.0
        assert valid.max() <= 1.0

    def test_ingreso_mensual_positive(self, sample_dataset):
        assert (sample_dataset["ingreso_mensual"] > 0).all()

    def test_monto_solicitado_range(self, sample_dataset):
        assert sample_dataset["monto_solicitado"].min() >= 500.0
        assert sample_dataset["monto_solicitado"].max() <= 50000.0

    def test_plazo_meses_valid_values(self, sample_dataset):
        valid_plazos = {6, 12, 18, 24, 36, 48, 60, 72, 84}
        assert set(sample_dataset["plazo_meses"].unique()).issubset(valid_plazos)


# ─── Tests de Categorías ─────────────────────────────────────────────────────

class TestCategories:
    """Tests que verifican las categorías de variables categóricas."""

    def test_estado_civil_categories(self, sample_dataset):
        valid = {"Soltero", "Casado", "Divorciado", "Viudo"}
        assert set(sample_dataset["estado_civil"].unique()).issubset(valid)

    def test_nivel_educativo_categories(self, sample_dataset):
        valid = {"Primaria", "Secundaria", "Universidad", "Posgrado"}
        assert set(sample_dataset["nivel_educativo"].unique()).issubset(valid)

    def test_tipo_vivienda_categories(self, sample_dataset):
        valid = {"Propia", "Arrendada", "Familiar"}
        assert set(sample_dataset["tipo_vivienda"].unique()).issubset(valid)

    def test_tipo_contrato_categories(self, sample_dataset):
        valid = {"Indefinido", "Temporal", "Independiente"}
        assert set(sample_dataset["tipo_contrato"].unique()).issubset(valid)

    def test_tipo_prestamo_categories(self, sample_dataset):
        valid = {"Personal", "Hipotecario", "Automotriz", "Tarjeta"}
        assert set(sample_dataset["tipo_prestamo"].unique()).issubset(valid)


# ─── Tests de Desbalanceo de Clases ──────────────────────────────────────────

class TestClassImbalance:
    """Tests que verifican el desbalanceo de clases objetivo."""

    def test_default_rate_within_range(self, sample_dataset):
        """Tasa de incumplimiento debe estar entre 15% y 25%."""
        rate = sample_dataset["incumplimiento"].mean()
        assert 0.15 <= rate <= 0.25, f"Tasa de incumplimiento: {rate:.2%}"

    def test_majority_class_dominates(self, sample_dataset):
        """La clase mayoritaria (no incumplimiento) debe superar el 70%."""
        paid_rate = 1 - sample_dataset["incumplimiento"].mean()
        assert paid_rate >= 0.70


# ─── Tests de Valores Nulos ───────────────────────────────────────────────────

class TestMissingValues:
    """Tests que verifican la inyección de valores nulos."""

    def test_missing_values_exist(self, sample_dataset):
        """El dataset debe tener algunos valores nulos (inyectados intencionalmente)."""
        assert sample_dataset.isnull().sum().sum() > 0

    def test_label_has_no_nulls(self, sample_dataset):
        """El label de incumplimiento NO debe tener valores nulos."""
        assert sample_dataset["incumplimiento"].isnull().sum() == 0

    def test_nullable_columns_have_nulls(self, sample_dataset):
        """Al menos una de las columnas nullable debe tener algún nulo."""
        nullable = ["score_buro", "meses_mora_maxima", "consultas_buro_6m",
                    "utilizacion_credito", "antiguedad_laboral"]
        total_nulls = sample_dataset[nullable].isnull().sum().sum()
        assert total_nulls > 0


# ─── Tests de Reproducibilidad ───────────────────────────────────────────────

class TestReproducibility:
    """Tests que verifican que el generador es determinístico con misma semilla."""

    def test_same_seed_same_output(self, tmp_path):
        """Con la misma semilla, el dataset debe ser idéntico."""
        df1 = generate_dataset(
            n_samples=100, output_dir=str(tmp_path),
            output_filename="rep1.csv", random_seed=99
        )
        df2 = generate_dataset(
            n_samples=100, output_dir=str(tmp_path),
            output_filename="rep2.csv", random_seed=99
        )
        pd.testing.assert_frame_equal(df1, df2)
