"""
SCOREIA — Módulo 1: Balancer
================================
Wrapper para manejo de desbalanceo de clases con SMOTE.

PRINCIPIO CRÍTICO DE ML: SMOTE debe aplicarse SOLAMENTE sobre el conjunto
de entrenamiento, NUNCA sobre el test set ni dentro de validación cruzada
sin protección adecuada. Esta clase encapsula ese principio.

Se usa imblearn (imbalanced-learn) que extiende sklearn con la interfaz
fit_resample() en lugar del pipeline estándar de sklearn.

Uso:
    from module1_preprocessing.balancer import ClassBalancer
    balancer = ClassBalancer(method="smote", random_state=42)
    X_balanced, y_balanced = balancer.fit_resample(X_train, y_train)
"""

import logging
from typing import Optional, Tuple

import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTE, BorderlineSMOTE, ADASYN
from sklearn.base import BaseEstimator

logger = logging.getLogger("SCOREIA.Balancer")


class ClassBalancer(BaseEstimator):
    """
    Wrapper para estrategias de balanceo de clases.

    Estrategias disponibles:
      - 'smote': SMOTE clásico (default para SCOREIA)
      - 'borderline': Borderline-SMOTE (genera sintéticos solo en frontera)
      - 'adasyn': ADASYN (adaptativo según densidad)

    IMPORTANTE:
      - Este transformador solo debe aplicarse sobre TRAIN SET
      - En K-Fold CV, usar imblearn.pipeline.Pipeline para que SMOTE
        se aplique dentro de cada fold de entrenamiento

    Attributes:
        method (str): Estrategia de balanceo.
        sampling_strategy: Estrategia de muestreo para SMOTE.
        k_neighbors (int): Número de vecinos para interpolación SMOTE.
        random_state (int): Semilla para reproducibilidad.
        sampler_: Instancia del sampler de imblearn ajustado.
        original_distribution_ (dict): Distribución original de clases.
        resampled_distribution_ (dict): Distribución tras balanceo.
    """

    AVAILABLE_METHODS = {
        "smote":      SMOTE,
        "borderline": BorderlineSMOTE,
        "adasyn":     ADASYN,
    }

    def __init__(
        self,
        method: str = "smote",
        sampling_strategy: str = "minority",
        k_neighbors: int = 5,
        random_state: int = 42,
    ):
        if method not in self.AVAILABLE_METHODS:
            raise ValueError(
                f"Metodo '{method}' no soportado. "
                f"Opciones: {list(self.AVAILABLE_METHODS.keys())}"
            )

        self.method = method
        self.sampling_strategy = sampling_strategy
        self.k_neighbors = k_neighbors
        self.random_state = random_state

        # Estado
        self.sampler_ = None
        self.original_distribution_: dict = {}
        self.resampled_distribution_: dict = {}

    def fit_resample(
        self,
        X: pd.DataFrame,
        y: pd.Series,
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Aplica balanceo de clases generando muestras sintéticas.

        Args:
            X: Features del conjunto de ENTRENAMIENTO (nunca test).
            y: Labels del conjunto de ENTRENAMIENTO.

        Returns:
            Tupla (X_balanced, y_balanced) con distribución equilibrada.
        """
        # ── Registrar distribución original ────────────────────────────
        self.original_distribution_ = y.value_counts().to_dict()
        n_original = len(y)
        logger.info(
            f"Distribucion original: {self.original_distribution_} "
            f"({n_original:,} muestras)"
        )

        # ── Crear instancia del sampler ────────────────────────────────
        SamplerClass = self.AVAILABLE_METHODS[self.method]

        sampler_kwargs = {
            "sampling_strategy": self.sampling_strategy,
            "random_state":      self.random_state,
        }

        # ADASYN no acepta k_neighbors directamente
        if self.method in ("smote", "borderline"):
            sampler_kwargs["k_neighbors"] = self.k_neighbors

        self.sampler_ = SamplerClass(**sampler_kwargs)

        # ── Aplicar resampling ─────────────────────────────────────────
        logger.info(
            f"Aplicando {self.method.upper()} "
            f"(k_neighbors={self.k_neighbors}, "
            f"strategy='{self.sampling_strategy}')..."
        )

        # SMOTE requiere datos numéricos — verificar
        non_numeric = X.select_dtypes(exclude=[np.number])
        if non_numeric.shape[1] > 0:
            raise ValueError(
                "SMOTE requiere datos 100% numericos. "
                "Aplique FeatureEncoder ANTES del balanceo. "
                f"Columnas no numericas: {list(non_numeric.columns)}"
            )

        X_resampled, y_resampled = self.sampler_.fit_resample(X, y)

        # ── Convertir de vuelta a DataFrame/Series ─────────────────────
        X_balanced = pd.DataFrame(X_resampled, columns=X.columns)
        y_balanced = pd.Series(y_resampled, name=y.name)

        # ── Registrar distribución balanceada ──────────────────────────
        self.resampled_distribution_ = y_balanced.value_counts().to_dict()
        n_synthetic = len(y_balanced) - n_original
        logger.info(
            f"Distribucion balanceada: {self.resampled_distribution_} "
            f"({len(y_balanced):,} muestras, +{n_synthetic:,} sinteticas)"
        )

        return X_balanced, y_balanced

    def get_balancing_summary(self) -> dict:
        """
        Retorna un resumen del proceso de balanceo.

        Returns:
            Diccionario con estadísticas antes/después del balanceo.
        """
        n_original = sum(self.original_distribution_.values())
        n_resampled = sum(self.resampled_distribution_.values())

        return {
            "method":         self.method,
            "k_neighbors":    self.k_neighbors,
            "strategy":       self.sampling_strategy,
            "before":         self.original_distribution_,
            "after":          self.resampled_distribution_,
            "n_original":     n_original,
            "n_resampled":    n_resampled,
            "n_synthetic":    n_resampled - n_original,
        }
