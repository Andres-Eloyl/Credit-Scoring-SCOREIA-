"""
SCOREIA — Módulo 1: Encoder
==============================
Transformador sklearn para codificación de variables categóricas:
  - One-Hot Encoding para variables nominales (estado_civil, tipo_vivienda, etc.)
  - Ordinal Encoding para nivel_educativo (Primaria < Secundaria < Universidad < Posgrado)

Diseñado como transformer compatible con sklearn.Pipeline.
Ajusta categorías en fit() y aplica en transform() para evitar data leakage.
Maneja categorías desconocidas en producción de forma segura.

Uso:
    from module1_preprocessing.encoder import FeatureEncoder
    encoder = FeatureEncoder()
    encoder.fit(X_train)
    X_encoded = encoder.transform(X_test)
"""

import logging
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

logger = logging.getLogger("SCOREIA.Encoder")


# =============================================================================
# DEFINICIÓN DE CODIFICACIONES
# =============================================================================

# Variables nominales → One-Hot Encoding
OHE_COLUMNS = [
    "estado_civil",
    "tipo_vivienda",
    "tipo_contrato",
    "tipo_prestamo",
]

# Variable ordinal → Encoding numérico con orden explícito
ORDINAL_MAPPING = {
    "nivel_educativo": {
        "Primaria":    0,
        "Secundaria":  1,
        "Universidad": 2,
        "Posgrado":    3,
    },
}


class FeatureEncoder(BaseEstimator, TransformerMixin):
    """
    Transformer sklearn para codificación de variables categóricas.

    Codificaciones aplicadas:
      - One-Hot Encoding para variables nominales
      - Ordinal Encoding para variables ordinales (nivel_educativo)

    Manejo de categorías desconocidas:
      - OHE: Todas las columnas dummy se ponen a 0 (categoría "ninguna")
      - Ordinal: Valor por defecto = -1 (flag de desconocido)

    Attributes:
        ohe_columns_ (list): Columnas categóricas para OHE (aprendidas en fit).
        ordinal_mapping_ (dict): Mapeos ordinales.
        ohe_categories_ (dict): Categorías aprendidas por columna en fit().
        encoded_columns_ (list): Lista de columnas finales tras encoding.
    """

    def __init__(
        self,
        ohe_columns: Optional[list] = None,
        ordinal_mapping: Optional[dict] = None,
        drop_first: bool = False,
    ):
        """
        Args:
            ohe_columns: Lista de columnas para One-Hot Encoding.
                         Default: OHE_COLUMNS definidas en el módulo.
            ordinal_mapping: Diccionario {columna: {valor: entero}}.
                             Default: ORDINAL_MAPPING del módulo.
            drop_first: Si True, elimina la primera categoría en OHE
                        para evitar multicolinealidad.
        """
        self.ohe_columns = ohe_columns or OHE_COLUMNS
        self.ordinal_mapping = ordinal_mapping or ORDINAL_MAPPING
        self.drop_first = drop_first

        # Aprendidos en fit()
        self.ohe_categories_: dict = {}
        self.encoded_columns_: list = []

    def fit(self, X: pd.DataFrame, y=None) -> "FeatureEncoder":
        """
        Aprende las categorías presentes en cada columna nominal.

        Args:
            X: DataFrame de entrenamiento.
            y: No utilizado.

        Returns:
            self
        """
        logger.info("Ajustando FeatureEncoder sobre datos de entrenamiento...")

        # ── Aprender categorías para OHE ──────────────────────────────
        self.ohe_categories_ = {}
        for col in self.ohe_columns:
            if col in X.columns:
                categories = sorted(X[col].astype(str).unique())
                self.ohe_categories_[col] = categories
                logger.debug(f"  OHE '{col}': {categories}")

        # ── Calcular la lista de columnas finales ─────────────────────
        self.encoded_columns_ = self._compute_output_columns(X)

        n_ohe = len(self.ohe_categories_)
        n_ord = len(self.ordinal_mapping)
        logger.info(
            f"FeatureEncoder ajustado: {n_ohe} columnas OHE, "
            f"{n_ord} columnas ordinales."
        )

        return self

    def transform(self, X: pd.DataFrame, y=None) -> pd.DataFrame:
        """
        Aplica codificación al DataFrame.

        Pipeline:
          1. Ordinal Encoding para nivel_educativo
          2. One-Hot Encoding para variables nominales
          3. Reordenar columnas para consistencia

        Args:
            X: DataFrame a codificar.

        Returns:
            DataFrame codificado.
        """
        X_enc = X.copy()

        # ── PASO 1: Ordinal Encoding ─────────────────────────────────
        for col, mapping in self.ordinal_mapping.items():
            if col in X_enc.columns:
                X_enc[col] = (
                    X_enc[col]
                    .astype(str)
                    .map(mapping)
                    .fillna(-1)    # Categorías desconocidas → -1
                    .astype(int)
                )
                logger.debug(
                    f"Ordinal encoding aplicado a '{col}': {mapping}"
                )

        # ── PASO 2: One-Hot Encoding ──────────────────────────────────
        for col, categories in self.ohe_categories_.items():
            if col not in X_enc.columns:
                continue

            col_str = X_enc[col].astype(str)

            cats_to_encode = categories
            if self.drop_first and len(cats_to_encode) > 1:
                cats_to_encode = cats_to_encode[1:]

            for cat in cats_to_encode:
                dummy_name = f"{col}_{cat}"
                X_enc[dummy_name] = (col_str == cat).astype(int)

            # Eliminar columna original
            X_enc = X_enc.drop(columns=[col])

        return X_enc

    def _compute_output_columns(self, X: pd.DataFrame) -> list:
        """Calcula la lista de columnas de salida tras encoding."""
        output_cols = []

        for col in X.columns:
            if col in self.ohe_categories_:
                categories = self.ohe_categories_[col]
                cats = categories[1:] if self.drop_first else categories
                output_cols.extend([f"{col}_{cat}" for cat in cats])
            else:
                output_cols.append(col)

        return output_cols

    def get_feature_names_out(self, input_features=None) -> list:
        """
        Retorna los nombres de las features de salida.
        Compatible con sklearn API.
        """
        return self.encoded_columns_
