"""
SCOREIA — Tests del Módulo 2: Ingeniería de Variables
=======================================================
Tests unitarios para RatioGenerator, WoEAnalyzer y FeatureSelector.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.module2_features.ratios import RatioGenerator
from src.module2_features.woe_encoder import WoEAnalyzer, _interpret_iv
from src.module2_features.feature_selector import FeatureSelector


# ═══════════════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def sample_df():
    """DataFrame sintético pequeño para tests rápidos."""
    np.random.seed(42)
    n = 300
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
    })


@pytest.fixture
def sample_target():
    """Target binario con ~20% incumplimiento."""
    np.random.seed(42)
    return pd.Series(
        np.random.choice([0, 0, 0, 0, 1], 300),
        name="incumplimiento",
    )


@pytest.fixture
def numeric_df(sample_df):
    """DataFrame solo numérico (sin categóricas) para tests de WoE y selector."""
    return sample_df.select_dtypes(include=[np.number])


# ═══════════════════════════════════════════════════════════════════════════
# TESTS: RatioGenerator
# ═══════════════════════════════════════════════════════════════════════════

class TestRatioGenerator:
    """Tests para RatioGenerator."""

    def test_generates_all_ratios_by_default(self, sample_df):
        """Por defecto genera los 7 ratios definidos."""
        gen = RatioGenerator()
        gen.fit(sample_df)
        X_new = gen.transform(sample_df)
        assert len(gen.generated_features_) == 7
        for ratio in RatioGenerator.ALL_RATIOS:
            assert ratio in X_new.columns

    def test_original_columns_preserved(self, sample_df):
        """Las columnas originales no se eliminan."""
        gen = RatioGenerator()
        X_new = gen.fit_transform(sample_df)
        for col in sample_df.columns:
            assert col in X_new.columns

    def test_more_columns_after_transform(self, sample_df):
        """El DataFrame tiene más columnas tras agregar ratios."""
        gen = RatioGenerator()
        X_new = gen.fit_transform(sample_df)
        assert X_new.shape[1] == sample_df.shape[1] + 7

    def test_selective_ratios(self, sample_df):
        """Se pueden generar solo ratios específicos."""
        gen = RatioGenerator(ratios_to_generate=["score_normalizado", "riesgo_compuesto"])
        X_new = gen.fit_transform(sample_df)
        assert "score_normalizado" in X_new.columns
        assert "riesgo_compuesto" in X_new.columns
        assert "cuota_estimada_ingreso" not in X_new.columns

    def test_score_normalizado_range(self, sample_df):
        """score_normalizado debe estar en [0, 1]."""
        gen = RatioGenerator(ratios_to_generate=["score_normalizado"])
        X_new = gen.fit_transform(sample_df)
        assert X_new["score_normalizado"].min() >= 0.0
        assert X_new["score_normalizado"].max() <= 1.0

    def test_riesgo_compuesto_range(self, sample_df):
        """riesgo_compuesto debe estar en [0, 100]."""
        gen = RatioGenerator(ratios_to_generate=["riesgo_compuesto"])
        X_new = gen.fit_transform(sample_df)
        assert X_new["riesgo_compuesto"].min() >= 0.0
        assert X_new["riesgo_compuesto"].max() <= 100.0

    def test_cuota_estimada_ingreso_capped(self, sample_df):
        """cuota_estimada_ingreso está capped en 2.0."""
        gen = RatioGenerator(ratios_to_generate=["cuota_estimada_ingreso"])
        X_new = gen.fit_transform(sample_df)
        assert X_new["cuota_estimada_ingreso"].max() <= 2.0

    def test_no_infinite_values(self, sample_df):
        """No deben quedar valores infinitos tras el transform."""
        gen = RatioGenerator()
        X_new = gen.fit_transform(sample_df)
        for ratio in gen.generated_features_:
            assert not np.isinf(X_new[ratio]).any(), f"Infinitos en {ratio}"

    def test_ratio_descriptions(self):
        """get_ratio_descriptions retorna diccionario completo."""
        gen = RatioGenerator()
        descs = gen.get_ratio_descriptions()
        assert len(descs) == 7
        for ratio in RatioGenerator.ALL_RATIOS:
            assert ratio in descs


# ═══════════════════════════════════════════════════════════════════════════
# TESTS: WoEAnalyzer
# ═══════════════════════════════════════════════════════════════════════════

class TestWoEAnalyzer:
    """Tests para WoEAnalyzer."""

    def test_fit_computes_iv_for_all_features(self, numeric_df, sample_target):
        """IV debe calcularse para cada feature numérica."""
        analyzer = WoEAnalyzer(n_bins=5)
        analyzer.fit(numeric_df, sample_target)
        assert len(analyzer.iv_values_) == numeric_df.shape[1]

    def test_iv_values_non_negative(self, numeric_df, sample_target):
        """IV nunca debe ser negativo."""
        analyzer = WoEAnalyzer(n_bins=5)
        analyzer.fit(numeric_df, sample_target)
        for feat, iv in analyzer.iv_values_.items():
            assert iv >= 0, f"IV negativo para {feat}: {iv}"

    def test_iv_summary_returns_dataframe(self, numeric_df, sample_target):
        """get_iv_summary retorna un DataFrame con las columnas esperadas."""
        analyzer = WoEAnalyzer(n_bins=5)
        analyzer.fit(numeric_df, sample_target)
        summary = analyzer.get_iv_summary()
        assert isinstance(summary, pd.DataFrame)
        assert "feature" in summary.columns
        assert "iv" in summary.columns
        assert "interpretacion" in summary.columns

    def test_iv_summary_sorted_descending(self, numeric_df, sample_target):
        """El resumen de IV debe estar ordenado de mayor a menor."""
        analyzer = WoEAnalyzer(n_bins=5)
        analyzer.fit(numeric_df, sample_target)
        summary = analyzer.get_iv_summary()
        iv_values = summary["iv"].tolist()
        assert iv_values == sorted(iv_values, reverse=True)

    def test_get_predictive_features(self, numeric_df, sample_target):
        """get_predictive_features retorna lista de features con IV >= umbral."""
        analyzer = WoEAnalyzer(n_bins=5)
        analyzer.fit(numeric_df, sample_target)
        predictive = analyzer.get_predictive_features(min_iv=0.02)
        assert isinstance(predictive, list)
        for feat in predictive:
            assert analyzer.iv_values_[feat] >= 0.02

    def test_woe_transform_returns_numeric(self, numeric_df, sample_target):
        """transform() debe retornar un DataFrame completamente numérico."""
        analyzer = WoEAnalyzer(n_bins=5)
        analyzer.fit(numeric_df, sample_target)
        X_woe = analyzer.transform(numeric_df)
        assert X_woe.select_dtypes(include=[np.number]).shape[1] == X_woe.shape[1]

    def test_interpret_iv_function(self):
        """_interpret_iv clasifica correctamente los valores de IV."""
        assert _interpret_iv(0.01) == "No predictivo"
        assert _interpret_iv(0.05) == "Predictivo debil"
        assert _interpret_iv(0.15) == "Predictivo medio"
        assert _interpret_iv(0.35) == "Predictivo fuerte"
        assert _interpret_iv(0.60) == "Sospechoso (overfitting?)"


# ═══════════════════════════════════════════════════════════════════════════
# TESTS: FeatureSelector
# ═══════════════════════════════════════════════════════════════════════════

class TestFeatureSelector:
    """Tests para FeatureSelector."""

    def test_selects_subset_of_features(self, numeric_df, sample_target):
        """El selector debe retornar un subconjunto de las features originales."""
        selector = FeatureSelector(min_iv=0.02, max_correlation=0.85)
        selector.fit(numeric_df, sample_target)
        X_sel = selector.transform(numeric_df)
        assert X_sel.shape[1] <= numeric_df.shape[1]
        for col in X_sel.columns:
            assert col in numeric_df.columns

    def test_drops_zero_variance(self, numeric_df, sample_target):
        """Features con varianza cero deben eliminarse."""
        df = numeric_df.copy()
        df["constante"] = 5.0  # Varianza = 0
        selector = FeatureSelector(min_iv=0.0, min_variance=0.001)
        selector.fit(df, sample_target)
        X_sel = selector.transform(df)
        assert "constante" not in X_sel.columns

    def test_drops_highly_correlated(self, sample_target):
        """De pares altamente correlacionados, elimina una."""
        np.random.seed(42)
        n = len(sample_target)
        col_a = np.random.normal(0, 1, n)
        col_b = col_a + np.random.normal(0, 0.01, n)  # Casi idéntica a col_a
        col_c = np.random.normal(5, 2, n)  # Independiente

        df = pd.DataFrame({"feature_a": col_a, "feature_b": col_b, "feature_c": col_c})

        selector = FeatureSelector(min_iv=0.0, max_correlation=0.90)
        selector.fit(df, sample_target)
        X_sel = selector.transform(df)

        # Una de las dos altamente correlacionadas debe haberse eliminado
        assert X_sel.shape[1] < 3

    def test_selection_report_generated(self, numeric_df, sample_target):
        """El reporte de selección se genera correctamente."""
        selector = FeatureSelector(min_iv=0.02)
        selector.fit(numeric_df, sample_target)
        report = selector.get_selection_report()
        assert isinstance(report, pd.DataFrame)
        assert "feature" in report.columns
        assert "status" in report.columns

    def test_get_feature_names_out(self, numeric_df, sample_target):
        """get_feature_names_out retorna las features seleccionadas."""
        selector = FeatureSelector(min_iv=0.02)
        selector.fit(numeric_df, sample_target)
        names = selector.get_feature_names_out()
        assert isinstance(names, list)
        assert len(names) == len(selector.selected_features_)

    def test_transform_preserves_row_count(self, numeric_df, sample_target):
        """transform() no debe cambiar el número de filas."""
        selector = FeatureSelector(min_iv=0.0)
        selector.fit(numeric_df, sample_target)
        X_sel = selector.transform(numeric_df)
        assert X_sel.shape[0] == numeric_df.shape[0]
