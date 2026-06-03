"""
SCOREIA — Módulo 1: Cleaner
==============================
Transformador sklearn para limpieza de datos:
  - Imputación de valores nulos (mediana para numéricos, moda para categóricos)
  - Detección y tratamiento de outliers mediante capping IQR
  - Validación de rangos post-limpieza

Diseñado como transformer compatible con sklearn.Pipeline.
Ajusta estadísticas en fit() y aplica en transform() para evitar data leakage.

Uso:
    from module1_preprocessing.cleaner import DataCleaner
    cleaner = DataCleaner(iqr_multiplier=1.5)
    cleaner.fit(X_train)
    X_clean = cleaner.transform(X_test)
"""

import logging
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

logger = logging.getLogger("SCOREIA.Cleaner")


# =============================================================================
# COLUMNAS DEL ESQUEMA SCOREIA
# =============================================================================

NUMERICAL_COLUMNS = [
    "edad", "ingreso_mensual", "antiguedad_laboral", "score_buro",
    "meses_mora_maxima", "num_creditos_activos", "consultas_buro_6m",
    "ratio_deuda_ingreso", "utilizacion_credito", "monto_solicitado",
    "plazo_meses",
]

CATEGORICAL_COLUMNS = [
    "estado_civil", "nivel_educativo", "tipo_vivienda",
    "tipo_contrato", "tipo_prestamo",
]


class DataCleaner(BaseEstimator, TransformerMixin):
    """
    Transformer sklearn para limpieza de datos crediticios.

    Pipeline de limpieza:
      1. Imputación de nulos (mediana / moda)
      2. Capping de outliers con IQR
      3. Forzado de tipos de datos

    IMPORTANTE: Ajusta estadísticas (medianas, modas, percentiles)
    solo en fit() sobre train set para evitar data leakage.

    Attributes:
        iqr_multiplier (float): Multiplicador IQR para capping de outliers.
        numerical_strategy (str): Estrategia de imputación numérica ('median').
        categorical_strategy (str): Estrategia de imputación categórica ('most_frequent').
        impute_values_ (dict): Valores de imputación aprendidos en fit().
        iqr_bounds_ (dict): Límites de capping aprendidos en fit().
    """

    def __init__(
        self,
        iqr_multiplier: float = 1.5,
        numerical_strategy: str = "median",
        categorical_strategy: str = "most_frequent",
    ):
        self.iqr_multiplier = iqr_multiplier
        self.numerical_strategy = numerical_strategy
        self.categorical_strategy = categorical_strategy

        # Aprendidos en fit()
        self.impute_values_: dict = {}
        self.iqr_bounds_: dict = {}

    def fit(self, X: pd.DataFrame, y=None) -> "DataCleaner":
        """
        Aprende estadísticas de imputación y capping del conjunto de entrenamiento.

        Args:
            X: DataFrame de entrenamiento.
            y: No utilizado (compatibilidad con sklearn API).

        Returns:
            self
        """
        logger.info("Ajustando DataCleaner sobre datos de entrenamiento...")

        # ── Aprender valores de imputación ─────────────────────────────
        self.impute_values_ = {}

        for col in NUMERICAL_COLUMNS:
            if col in X.columns and X[col].isnull().any():
                if self.numerical_strategy == "median":
                    self.impute_values_[col] = X[col].median()
                elif self.numerical_strategy == "mean":
                    self.impute_values_[col] = X[col].mean()
                else:
                    self.impute_values_[col] = X[col].median()
                logger.debug(
                    f"  Imputacion {col}: {self.numerical_strategy} = "
                    f"{self.impute_values_[col]:.4f}"
                )

        for col in CATEGORICAL_COLUMNS:
            if col in X.columns and X[col].isnull().any():
                self.impute_values_[col] = X[col].mode().iloc[0]
                logger.debug(
                    f"  Imputacion {col}: moda = {self.impute_values_[col]}"
                )

        # ── Aprender límites de capping IQR ────────────────────────────
        self.iqr_bounds_ = {}
        capping_cols = [
            "ingreso_mensual", "antiguedad_laboral", "meses_mora_maxima",
            "num_creditos_activos", "consultas_buro_6m",
            "ratio_deuda_ingreso", "utilizacion_credito",
            "monto_solicitado",
        ]

        for col in capping_cols:
            if col in X.columns:
                q1 = X[col].quantile(0.25)
                q3 = X[col].quantile(0.75)
                iqr = q3 - q1
                lower = q1 - self.iqr_multiplier * iqr
                upper = q3 + self.iqr_multiplier * iqr

                # Ajustar lower para que no sea negativo en variables que no lo permiten
                if col in [
                    "ingreso_mensual", "antiguedad_laboral", "meses_mora_maxima",
                    "num_creditos_activos", "consultas_buro_6m",
                    "utilizacion_credito", "monto_solicitado",
                ]:
                    lower = max(lower, 0.0)

                self.iqr_bounds_[col] = {"lower": lower, "upper": upper}
                logger.debug(
                    f"  Capping {col}: [{lower:.2f}, {upper:.2f}]"
                )

        n_impute = len(self.impute_values_)
        n_cap = len(self.iqr_bounds_)
        logger.info(
            f"DataCleaner ajustado: {n_impute} reglas de imputacion, "
            f"{n_cap} reglas de capping."
        )

        return self

    def transform(self, X: pd.DataFrame, y=None) -> pd.DataFrame:
        """
        Aplica limpieza al DataFrame usando estadísticas aprendidas en fit().

        Pipeline:
          1. Imputar nulos
          2. Capping de outliers
          3. Forzar tipos de datos

        Args:
            X: DataFrame a limpiar.

        Returns:
            DataFrame limpio (copia, no modifica el original).
        """
        X_clean = X.copy()

        # ── PASO 1: Imputación ─────────────────────────────────────────
        n_imputed = 0
        for col, fill_value in self.impute_values_.items():
            if col in X_clean.columns:
                n_null = X_clean[col].isnull().sum()
                if n_null > 0:
                    X_clean[col] = X_clean[col].fillna(fill_value)
                    n_imputed += n_null

        if n_imputed > 0:
            logger.info(f"Imputados {n_imputed:,} valores nulos.")

        # ── PASO 2: Capping de outliers ─────────────────────────────────
        n_capped = 0
        for col, bounds in self.iqr_bounds_.items():
            if col in X_clean.columns:
                lower, upper = bounds["lower"], bounds["upper"]
                mask_low = X_clean[col] < lower
                mask_high = X_clean[col] > upper
                n_out = mask_low.sum() + mask_high.sum()
                if n_out > 0:
                    X_clean[col] = X_clean[col].clip(lower=lower, upper=upper)
                    n_capped += n_out

        if n_capped > 0:
            logger.info(f"Outliers capped: {n_capped:,} valores ajustados por IQR.")

        # ── PASO 3: Forzar tipos ───────────────────────────────────────
        for col in CATEGORICAL_COLUMNS:
            if col in X_clean.columns:
                X_clean[col] = X_clean[col].astype(str)

        return X_clean

    def get_cleaning_summary(self) -> dict:
        """
        Retorna un resumen de las reglas de limpieza aprendidas.

        Returns:
            Diccionario con reglas de imputación y capping.
        """
        return {
            "imputation_rules": self.impute_values_.copy(),
            "capping_rules": {
                col: {
                    "lower": round(b["lower"], 4),
                    "upper": round(b["upper"], 4),
                }
                for col, b in self.iqr_bounds_.items()
            },
        }
