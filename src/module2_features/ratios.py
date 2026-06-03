"""
SCOREIA — Módulo 2: Ratios Financieros
=========================================
Transformador sklearn que genera variables derivadas (feature engineering)
a partir de las 16 variables base del dataset SCOREIA.

Ratios implementados:
  - cuota_estimada_ingreso: Cuota mensual estimada / Ingreso mensual
  - monto_ingreso_ratio: Monto solicitado / Ingreso mensual
  - score_normalizado: Score de buró normalizado al rango [0, 1]
  - antiguedad_edad_ratio: Antigüedad laboral / Edad (estabilidad laboral)
  - deuda_utilizacion_producto: Interacción deuda/ingreso * utilización de crédito
  - consultas_creditos_ratio: Consultas al buró / (Créditos activos + 1)
  - riesgo_compuesto: Score compuesto ponderado de riesgo

Principio: fit() no aprende nada (ratios son determinísticos),
pero se mantiene la interfaz sklearn para encadenarse en Pipeline.

Uso:
    from module2_features.ratios import RatioGenerator
    ratio_gen = RatioGenerator()
    X_enriched = ratio_gen.transform(X)
"""

import logging
from typing import List, Optional

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

logger = logging.getLogger("SCOREIA.Ratios")


class RatioGenerator(BaseEstimator, TransformerMixin):
    """
    Transformer sklearn que genera variables financieras derivadas.

    Genera ratios, normalizaciones e interacciones a partir de las
    16 variables base de SCOREIA. Estas variables derivadas capturan
    relaciones no lineales que mejoran el poder predictivo del modelo.

    Attributes:
        ratios_to_generate (list): Lista de ratios a generar.
            Default: todos los disponibles.
        generated_features_ (list): Features generadas tras transform().
    """

    # Todos los ratios disponibles
    ALL_RATIOS = [
        "cuota_estimada_ingreso",
        "monto_ingreso_ratio",
        "score_normalizado",
        "antiguedad_edad_ratio",
        "deuda_utilizacion_producto",
        "consultas_creditos_ratio",
        "riesgo_compuesto",
    ]

    def __init__(self, ratios_to_generate: Optional[List[str]] = None):
        """
        Args:
            ratios_to_generate: Lista de ratios a generar. Si None, genera todos.
        """
        self.ratios_to_generate = ratios_to_generate or self.ALL_RATIOS
        self.generated_features_: list = []

    def fit(self, X: pd.DataFrame, y=None) -> "RatioGenerator":
        """
        No aprende nada (ratios son determinísticos). Mantiene la interfaz sklearn.

        Args:
            X: DataFrame de entrenamiento.
            y: No utilizado.

        Returns:
            self
        """
        logger.info(
            f"RatioGenerator configurado: {len(self.ratios_to_generate)} ratios a generar."
        )
        return self

    def transform(self, X: pd.DataFrame, y=None) -> pd.DataFrame:
        """
        Genera las variables derivadas y las agrega al DataFrame.

        Args:
            X: DataFrame con las features originales.

        Returns:
            DataFrame con las nuevas columnas agregadas.
        """
        X_new = X.copy()
        self.generated_features_ = []

        for ratio_name in self.ratios_to_generate:
            generator_method = getattr(self, f"_compute_{ratio_name}", None)
            if generator_method is None:
                logger.warning(f"Ratio '{ratio_name}' no implementado, se omite.")
                continue

            try:
                X_new[ratio_name] = generator_method(X_new)
                self.generated_features_.append(ratio_name)
            except KeyError as e:
                logger.warning(
                    f"No se pudo generar '{ratio_name}': columna {e} no encontrada."
                )

        logger.info(
            f"RatioGenerator: {len(self.generated_features_)} variables derivadas generadas: "
            f"{self.generated_features_}"
        )

        return X_new

    # ═══════════════════════════════════════════════════════════════════
    # RATIOS FINANCIEROS INDIVIDUALES
    # ═══════════════════════════════════════════════════════════════════

    @staticmethod
    def _compute_cuota_estimada_ingreso(df: pd.DataFrame) -> pd.Series:
        """
        Cuota mensual estimada como proporción del ingreso.
        Formula: monto_solicitado / (plazo_meses * ingreso_mensual)

        Interpretación: Qué fracción del ingreso mensual se destina
        a pagar la cuota del préstamo. Valores altos = mayor riesgo.
        """
        denominator = df["plazo_meses"] * df["ingreso_mensual"]
        ratio = df["monto_solicitado"] / denominator.replace(0, np.nan)
        return ratio.clip(upper=2.0).round(6)  # Cap en 200% como máximo razonable

    @staticmethod
    def _compute_monto_ingreso_ratio(df: pd.DataFrame) -> pd.Series:
        """
        Monto solicitado como múltiplo del ingreso mensual.
        Formula: monto_solicitado / ingreso_mensual

        Interpretación: Cuántos meses de ingreso equivale el préstamo.
        Valores muy altos indican solicitudes desproporcionadas.
        """
        ratio = df["monto_solicitado"] / df["ingreso_mensual"].replace(0, np.nan)
        return ratio.clip(upper=50.0).round(4)  # Cap en 50x ingreso

    @staticmethod
    def _compute_score_normalizado(df: pd.DataFrame) -> pd.Series:
        """
        Score de buró normalizado al rango [0, 1].
        Formula: (score_buro - 300) / 550

        Interpretación: 0 = peor score posible, 1 = mejor score posible.
        Facilita la interpretación y comparabilidad.
        """
        return ((df["score_buro"] - 300) / 550).clip(0, 1).round(4)

    @staticmethod
    def _compute_antiguedad_edad_ratio(df: pd.DataFrame) -> pd.Series:
        """
        Estabilidad laboral relativa a la edad.
        Formula: antiguedad_laboral / (edad * 12)

        Interpretación: Qué proporción de su vida adulta ha trabajado
        en el empleo actual. Valores altos = mayor estabilidad.
        """
        edad_meses = df["edad"] * 12
        ratio = df["antiguedad_laboral"] / edad_meses.replace(0, np.nan)
        return ratio.clip(0, 1.0).round(4)

    @staticmethod
    def _compute_deuda_utilizacion_producto(df: pd.DataFrame) -> pd.Series:
        """
        Interacción entre ratio deuda/ingreso y utilización de crédito.
        Formula: ratio_deuda_ingreso * utilizacion_credito

        Interpretación: Captura el efecto multiplicativo de tener
        alta deuda Y alta utilización simultáneamente (doble riesgo).
        """
        return (df["ratio_deuda_ingreso"] * df["utilizacion_credito"]).round(6)

    @staticmethod
    def _compute_consultas_creditos_ratio(df: pd.DataFrame) -> pd.Series:
        """
        Intensidad de búsqueda de crédito.
        Formula: consultas_buro_6m / (num_creditos_activos + 1)

        Interpretación: Muchas consultas con pocos créditos activos
        sugiere rechazos previos (señal de riesgo).
        """
        denominator = df["num_creditos_activos"] + 1  # +1 para evitar div/0
        return (df["consultas_buro_6m"] / denominator).round(4)

    @staticmethod
    def _compute_riesgo_compuesto(df: pd.DataFrame) -> pd.Series:
        """
        Índice compuesto de riesgo crediticio (0-100 normalizado).
        Pondera múltiples señales de riesgo en un solo indicador.

        Componentes ponderados:
          - Score buró invertido (40%): Menor score = mayor riesgo
          - Ratio deuda/ingreso (25%): Mayor ratio = mayor riesgo
          - Utilización crédito (15%): Mayor utilización = mayor riesgo
          - Mora máxima normalizada (20%): Más meses = mayor riesgo

        Interpretación: 0 = bajo riesgo, 100 = alto riesgo.
        """
        # Normalizar componentes al rango [0, 1] donde 1 = mayor riesgo
        score_inv = 1 - (df["score_buro"] - 300).clip(0, 550) / 550
        dti_norm = df["ratio_deuda_ingreso"].clip(0, 1.5) / 1.5
        util_norm = df["utilizacion_credito"].clip(0, 1.0)
        mora_norm = df["meses_mora_maxima"].clip(0, 24) / 24

        riesgo = (
            0.40 * score_inv
            + 0.25 * dti_norm
            + 0.15 * util_norm
            + 0.20 * mora_norm
        )

        return (riesgo * 100).round(2)

    # ═══════════════════════════════════════════════════════════════════
    # UTILIDADES
    # ═══════════════════════════════════════════════════════════════════

    def get_feature_names_out(self, input_features=None) -> list:
        """Retorna los nombres de features generadas (sklearn API)."""
        return self.generated_features_

    def get_ratio_descriptions(self) -> dict:
        """Retorna descripciones de cada ratio para documentación."""
        return {
            "cuota_estimada_ingreso":      "Cuota mensual estimada / Ingreso mensual",
            "monto_ingreso_ratio":         "Monto solicitado / Ingreso mensual (multiplo)",
            "score_normalizado":           "Score buro normalizado [0=peor, 1=mejor]",
            "antiguedad_edad_ratio":       "Antiguedad laboral / Edad (estabilidad)",
            "deuda_utilizacion_producto":  "Interaccion deuda/ingreso * utilizacion",
            "consultas_creditos_ratio":    "Consultas buro / (Creditos activos + 1)",
            "riesgo_compuesto":            "Indice compuesto de riesgo [0=bajo, 100=alto]",
        }
