"""
SCOREIA — Módulo 2: Selector de Features
============================================
Selector de variables basado en múltiples criterios:
  1. Information Value (IV): Retener solo features con IV >= umbral
  2. Correlación: Eliminar features altamente correlacionadas (multicolinealidad)
  3. Varianza mínima: Eliminar features con varianza casi nula

Compatible con sklearn Pipeline. Aprende criterios en fit() y aplica en transform().

Uso:
    from module2_features.feature_selector import FeatureSelector
    selector = FeatureSelector(min_iv=0.02, max_correlation=0.85)
    selector.fit(X_train, y_train)
    X_selected = selector.transform(X_test)
"""

import logging
from typing import List, Optional, Dict

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

from .woe_encoder import WoEAnalyzer

logger = logging.getLogger("SCOREIA.FeatureSelector")


class FeatureSelector(BaseEstimator, TransformerMixin):
    """
    Selector de features basado en IV, correlación y varianza.

    Pipeline de selección (en este orden):
      1. Eliminar features con varianza casi nula (< min_variance)
      2. Eliminar features no predictivas (IV < min_iv)
      3. De pares altamente correlacionados, eliminar la de menor IV

    Attributes:
        min_iv (float): IV mínimo para retener una feature (default 0.02).
        max_correlation (float): Correlación máxima permitida entre features.
        min_variance (float): Varianza mínima para retener una feature.
        iv_analyzer (WoEAnalyzer): Instancia del analyzer WoE/IV.
        selected_features_ (list): Features seleccionadas tras fit().
        dropped_features_ (dict): Features eliminadas y razón de eliminación.
        correlation_matrix_ (pd.DataFrame): Matriz de correlación aprendida.
    """

    def __init__(
        self,
        min_iv: float = 0.02,
        max_correlation: float = 0.85,
        min_variance: float = 0.001,
        n_bins_woe: int = 10,
        categorical_columns: Optional[List[str]] = None,
    ):
        self.min_iv = min_iv
        self.max_correlation = max_correlation
        self.min_variance = min_variance
        self.n_bins_woe = n_bins_woe
        self.categorical_columns = categorical_columns

        # Aprendidos en fit()
        self.iv_analyzer: Optional[WoEAnalyzer] = None
        self.selected_features_: List[str] = []
        self.dropped_features_: Dict[str, str] = {}
        self.correlation_matrix_: Optional[pd.DataFrame] = None
        self.feature_report_: List[dict] = []

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "FeatureSelector":
        """
        Analiza las features y selecciona las mejores.

        Args:
            X: Features de entrenamiento.
            y: Target binario (0/1).

        Returns:
            self
        """
        logger.info(
            f"FeatureSelector: analizando {X.shape[1]} features "
            f"(min_iv={self.min_iv}, max_corr={self.max_correlation})..."
        )

        candidates = list(X.columns)
        self.dropped_features_ = {}

        # ── PASO 1: Filtro por varianza ────────────────────────────────
        candidates = self._filter_by_variance(X, candidates)

        # ── PASO 2: Calcular IV (solo para las columnas numéricas) ─────
        numeric_candidates = [
            c for c in candidates
            if pd.api.types.is_numeric_dtype(X[c])
        ]

        self.iv_analyzer = WoEAnalyzer(
            n_bins=self.n_bins_woe,
            categorical_columns=self.categorical_columns or [],
        )

        if numeric_candidates:
            self.iv_analyzer.fit(X[numeric_candidates], y)
            candidates = self._filter_by_iv(candidates, numeric_candidates)

        # ── PASO 3: Filtro por correlación ─────────────────────────────
        numeric_remaining = [
            c for c in candidates
            if pd.api.types.is_numeric_dtype(X[c])
        ]
        if numeric_remaining:
            candidates = self._filter_by_correlation(X, candidates, numeric_remaining)

        self.selected_features_ = candidates

        # ── Generar reporte ─────────────────────────────────────────────
        self._build_report(X)

        n_orig = X.shape[1]
        n_sel = len(self.selected_features_)
        n_drop = len(self.dropped_features_)
        logger.info(
            f"FeatureSelector: {n_sel}/{n_orig} features seleccionadas, "
            f"{n_drop} eliminadas."
        )

        return self

    def transform(self, X: pd.DataFrame, y=None) -> pd.DataFrame:
        """
        Retiene solo las features seleccionadas en fit().

        Args:
            X: DataFrame a filtrar.

        Returns:
            DataFrame con solo las features seleccionadas.
        """
        # Retener solo las columnas seleccionadas que existan en X
        available = [c for c in self.selected_features_ if c in X.columns]
        return X[available]

    # ═══════════════════════════════════════════════════════════════════
    # FILTROS INDIVIDUALES
    # ═══════════════════════════════════════════════════════════════════

    def _filter_by_variance(
        self,
        X: pd.DataFrame,
        candidates: List[str],
    ) -> List[str]:
        """Elimina features con varianza menor al umbral."""
        kept = []
        for col in candidates:
            if pd.api.types.is_numeric_dtype(X[col]):
                var = X[col].var()
                if var < self.min_variance:
                    self.dropped_features_[col] = (
                        f"Varianza insuficiente ({var:.6f} < {self.min_variance})"
                    )
                    continue
            kept.append(col)

        n_dropped = len(candidates) - len(kept)
        if n_dropped > 0:
            logger.info(f"  Varianza: {n_dropped} features eliminadas.")
        return kept

    def _filter_by_iv(
        self,
        candidates: List[str],
        numeric_candidates: List[str],
    ) -> List[str]:
        """Elimina features numéricas con IV menor al umbral."""
        kept = []
        for col in candidates:
            if col in numeric_candidates:
                iv = self.iv_analyzer.iv_values_.get(col, 0.0)
                if iv < self.min_iv:
                    self.dropped_features_[col] = (
                        f"IV insuficiente ({iv:.4f} < {self.min_iv})"
                    )
                    continue
            kept.append(col)

        n_dropped = len(candidates) - len(kept)
        if n_dropped > 0:
            logger.info(f"  IV: {n_dropped} features eliminadas (IV < {self.min_iv}).")
        return kept

    def _filter_by_correlation(
        self,
        X: pd.DataFrame,
        candidates: List[str],
        numeric_cols: List[str],
    ) -> List[str]:
        """
        De pares altamente correlacionados, elimina la de menor IV.
        """
        corr_matrix = X[numeric_cols].corr().abs()
        self.correlation_matrix_ = corr_matrix

        to_drop = set()
        processed = set()

        for i, col_i in enumerate(numeric_cols):
            if col_i in to_drop:
                continue
            for j, col_j in enumerate(numeric_cols):
                if i >= j or col_j in to_drop:
                    continue

                pair = tuple(sorted([col_i, col_j]))
                if pair in processed:
                    continue
                processed.add(pair)

                corr_val = corr_matrix.loc[col_i, col_j]
                if corr_val >= self.max_correlation:
                    # Eliminar la de menor IV
                    iv_i = self.iv_analyzer.iv_values_.get(col_i, 0.0)
                    iv_j = self.iv_analyzer.iv_values_.get(col_j, 0.0)

                    drop_col = col_j if iv_i >= iv_j else col_i
                    keep_col = col_i if iv_i >= iv_j else col_j

                    to_drop.add(drop_col)
                    self.dropped_features_[drop_col] = (
                        f"Alta correlacion con '{keep_col}' "
                        f"(r={corr_val:.3f} >= {self.max_correlation}) "
                        f"y menor IV"
                    )

        kept = [c for c in candidates if c not in to_drop]

        if to_drop:
            logger.info(
                f"  Correlacion: {len(to_drop)} features eliminadas "
                f"(|r| >= {self.max_correlation})."
            )

        return kept

    # ═══════════════════════════════════════════════════════════════════
    # REPORTES
    # ═══════════════════════════════════════════════════════════════════

    def _build_report(self, X: pd.DataFrame) -> None:
        """Construye el reporte detallado de selección de features."""
        self.feature_report_ = []
        for col in X.columns:
            iv = self.iv_analyzer.iv_values_.get(col, None) if self.iv_analyzer else None
            status = "Seleccionada" if col in self.selected_features_ else "Eliminada"
            reason = self.dropped_features_.get(col, "")

            self.feature_report_.append({
                "feature": col,
                "iv": round(iv, 4) if iv is not None else None,
                "status": status,
                "razon_eliminacion": reason,
            })

    def get_selection_report(self) -> pd.DataFrame:
        """Retorna un DataFrame con el reporte de selección."""
        return pd.DataFrame(self.feature_report_)

    def print_selection_report(self) -> None:
        """Imprime el reporte de selección formateado."""
        report = self.get_selection_report()

        print("\n" + "=" * 75)
        print("  SCOREIA -- REPORTE DE SELECCION DE FEATURES")
        print("=" * 75)
        print(
            f"  {'Feature':<32s} {'IV':>7s}   {'Status':<12s} "
            f"{'Razon'}"
        )
        print("-" * 75)

        for _, row in report.iterrows():
            iv_str = f"{row['iv']:.4f}" if row["iv"] is not None else "  N/A"
            marker = "[+]" if row["status"] == "Seleccionada" else "[-]"
            print(
                f"  {marker} {row['feature']:<28s} {iv_str:>7s}   "
                f"{row['status']:<12s} {row['razon_eliminacion']}"
            )

        print("-" * 75)
        n_sel = sum(1 for _, r in report.iterrows() if r["status"] == "Seleccionada")
        print(f"  Total: {n_sel} seleccionadas / {len(report)} evaluadas")
        print("=" * 75 + "\n")

    def get_feature_names_out(self, input_features=None) -> list:
        """Retorna las features seleccionadas (sklearn API)."""
        return self.selected_features_
