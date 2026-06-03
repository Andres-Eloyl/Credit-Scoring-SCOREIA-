"""
SCOREIA — Módulo 2: Weight of Evidence (WoE) & Information Value (IV)
=======================================================================
Calcula WoE e IV para cada variable predictora del dataset SCOREIA.

Conceptos:
  - WoE: Mide la fuerza predictiva de cada categoría/bin de una variable
    respecto al target. WoE = ln(Dist_Good / Dist_Bad).
  - IV: Mide el poder predictivo TOTAL de una variable.
    IV = Σ (Dist_Good - Dist_Bad) * WoE

Interpretación del IV:
  IV < 0.02  → No predictivo (descartar)
  0.02-0.10  → Predictivo débil
  0.10-0.30  → Predictivo medio
  0.30-0.50  → Predictivo fuerte
  IV > 0.50  → Sospechoso (posible overfitting o leakage)

Para variables numéricas, se discretizan en bins (quantile-based)
antes de calcular WoE.

Uso:
    from module2_features.woe_encoder import WoEAnalyzer
    analyzer = WoEAnalyzer(n_bins=10)
    analyzer.fit(X_train, y_train)
    iv_table = analyzer.get_iv_summary()
    X_woe = analyzer.transform(X_test)
"""

import logging
from typing import Optional, List, Dict, Tuple

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

logger = logging.getLogger("SCOREIA.WoE")


# Interpretación estándar de Information Value
IV_INTERPRETATION = {
    (0.00, 0.02): "No predictivo",
    (0.02, 0.10): "Predictivo debil",
    (0.10, 0.30): "Predictivo medio",
    (0.30, 0.50): "Predictivo fuerte",
    (0.50, float("inf")): "Sospechoso (overfitting?)",
}


def _interpret_iv(iv_value: float) -> str:
    """Retorna la interpretación textual de un valor de IV."""
    for (low, high), label in IV_INTERPRETATION.items():
        if low <= iv_value < high:
            return label
    return "Desconocido"


class WoEAnalyzer(BaseEstimator, TransformerMixin):
    """
    Calcula Weight of Evidence (WoE) e Information Value (IV)
    para cada feature del dataset.

    Para variables categóricas: WoE por categoría directa.
    Para variables numéricas: WoE por bin (quantile-based binning).

    Attributes:
        n_bins (int): Número de bins para discretizar variables numéricas.
        min_samples_bin (int): Mínimo de muestras por bin.
        regularization (float): Smoothing para evitar log(0).
        categorical_columns (list): Columnas a tratar como categóricas.
        woe_tables_ (dict): Tablas WoE por columna, aprendidas en fit().
        iv_values_ (dict): Valores de IV por columna, aprendidos en fit().
        bin_edges_ (dict): Bordes de bins para variables numéricas.
    """

    def __init__(
        self,
        n_bins: int = 10,
        min_samples_bin: int = 20,
        regularization: float = 0.5,
        categorical_columns: Optional[List[str]] = None,
    ):
        self.n_bins = n_bins
        self.min_samples_bin = min_samples_bin
        self.regularization = regularization
        self.categorical_columns = categorical_columns or []

        # Aprendidos en fit()
        self.woe_tables_: Dict[str, pd.DataFrame] = {}
        self.iv_values_: Dict[str, float] = {}
        self.bin_edges_: Dict[str, np.ndarray] = {}

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "WoEAnalyzer":
        """
        Calcula WoE e IV para cada columna usando datos de entrenamiento.

        Args:
            X: Features de entrenamiento.
            y: Target binario (0/1) de entrenamiento.

        Returns:
            self
        """
        logger.info("Calculando WoE e IV para todas las features...")

        # Auto-detectar categóricas si no se especifican
        if not self.categorical_columns:
            self.categorical_columns = list(
                X.select_dtypes(
                    include=["object", "category", "str", "string"]
                ).columns
            )

        total_good = (y == 0).sum()
        total_bad = (y == 1).sum()

        for col in X.columns:
            try:
                is_categorical = col in self.categorical_columns

                if is_categorical:
                    woe_table = self._compute_woe_categorical(
                        X[col], y, total_good, total_bad
                    )
                else:
                    woe_table = self._compute_woe_numerical(
                        X[col], y, total_good, total_bad, col
                    )

                self.woe_tables_[col] = woe_table
                self.iv_values_[col] = woe_table["iv_component"].sum()

            except Exception as e:
                logger.warning(f"Error calculando WoE para '{col}': {e}")
                self.iv_values_[col] = 0.0

        # Ordenar por IV descendente
        self.iv_values_ = dict(
            sorted(self.iv_values_.items(), key=lambda x: -x[1])
        )

        n_features = len(self.iv_values_)
        n_predictive = sum(1 for iv in self.iv_values_.values() if iv >= 0.02)
        logger.info(
            f"WoE/IV calculados para {n_features} features. "
            f"{n_predictive} son predictivas (IV >= 0.02)."
        )

        return self

    def transform(self, X: pd.DataFrame, y=None) -> pd.DataFrame:
        """
        Reemplaza cada valor por su WoE correspondiente.

        Esto crea una representación numérica donde cada valor refleja
        su poder predictivo respecto al target.

        Args:
            X: DataFrame a transformar.

        Returns:
            DataFrame con valores WoE.
        """
        X_woe = X.copy()

        for col in X.columns:
            if col not in self.woe_tables_:
                continue

            woe_table = self.woe_tables_[col]
            is_categorical = col in self.categorical_columns

            if is_categorical:
                woe_map = dict(zip(woe_table["bin"], woe_table["woe"]))
                X_woe[col] = X_woe[col].astype(str).map(woe_map).fillna(0.0)
            else:
                if col in self.bin_edges_:
                    edges = self.bin_edges_[col]
                    binned = pd.cut(
                        X_woe[col], bins=edges, labels=False,
                        include_lowest=True, duplicates="drop"
                    )
                    woe_map = dict(zip(range(len(woe_table)), woe_table["woe"]))
                    X_woe[col] = binned.map(woe_map).fillna(0.0)

        return X_woe

    def _compute_woe_categorical(
        self,
        series: pd.Series,
        y: pd.Series,
        total_good: int,
        total_bad: int,
    ) -> pd.DataFrame:
        """Calcula WoE para una variable categórica."""
        df_temp = pd.DataFrame({"feature": series.astype(str), "target": y})

        grouped = df_temp.groupby("feature")["target"].agg(["count", "sum"])
        grouped.columns = ["total", "bad"]
        grouped["good"] = grouped["total"] - grouped["bad"]

        # Regularización: sumar epsilon para evitar log(0)
        eps = self.regularization
        grouped["dist_good"] = (grouped["good"] + eps) / (total_good + eps * len(grouped))
        grouped["dist_bad"] = (grouped["bad"] + eps) / (total_bad + eps * len(grouped))

        grouped["woe"] = np.log(grouped["dist_good"] / grouped["dist_bad"])
        grouped["iv_component"] = (
            (grouped["dist_good"] - grouped["dist_bad"]) * grouped["woe"]
        )

        grouped = grouped.reset_index().rename(columns={"feature": "bin"})
        return grouped

    def _compute_woe_numerical(
        self,
        series: pd.Series,
        y: pd.Series,
        total_good: int,
        total_bad: int,
        col_name: str,
    ) -> pd.DataFrame:
        """Calcula WoE para una variable numérica (binning quantile-based)."""
        # Crear bins basados en cuantiles
        valid_mask = series.notna()
        series_valid = series[valid_mask]
        y_valid = y[valid_mask]

        try:
            binned, edges = pd.qcut(
                series_valid, q=self.n_bins,
                retbins=True, labels=False, duplicates="drop"
            )
        except ValueError:
            # Si hay muy pocos valores únicos, usar cut simple
            binned, edges = pd.cut(
                series_valid, bins=min(self.n_bins, series_valid.nunique()),
                retbins=True, labels=False, duplicates="drop"
            )

        self.bin_edges_[col_name] = edges

        df_temp = pd.DataFrame({"bin": binned, "target": y_valid})
        grouped = df_temp.groupby("bin")["target"].agg(["count", "sum"])
        grouped.columns = ["total", "bad"]
        grouped["good"] = grouped["total"] - grouped["bad"]

        # Regularización
        eps = self.regularization
        n_bins = len(grouped)
        grouped["dist_good"] = (grouped["good"] + eps) / (total_good + eps * n_bins)
        grouped["dist_bad"] = (grouped["bad"] + eps) / (total_bad + eps * n_bins)

        grouped["woe"] = np.log(grouped["dist_good"] / grouped["dist_bad"])
        grouped["iv_component"] = (
            (grouped["dist_good"] - grouped["dist_bad"]) * grouped["woe"]
        )

        grouped = grouped.reset_index()
        grouped["bin"] = grouped["bin"].astype(str)
        return grouped

    # ═══════════════════════════════════════════════════════════════════
    # REPORTES
    # ═══════════════════════════════════════════════════════════════════

    def get_iv_summary(self) -> pd.DataFrame:
        """
        Retorna un DataFrame resumen con IV por feature, ordenado descendentemente.

        Returns:
            DataFrame con columnas: feature, iv, interpretacion
        """
        rows = []
        for feature, iv in self.iv_values_.items():
            rows.append({
                "feature": feature,
                "iv": round(iv, 6),
                "interpretacion": _interpret_iv(iv),
            })

        return pd.DataFrame(rows)

    def get_predictive_features(self, min_iv: float = 0.02) -> List[str]:
        """
        Retorna las features con IV >= min_iv (predictivas).

        Args:
            min_iv: Umbral mínimo de IV.

        Returns:
            Lista de nombres de features predictivas ordenadas por IV.
        """
        return [
            feat for feat, iv in self.iv_values_.items()
            if iv >= min_iv
        ]

    def get_suspicious_features(self, max_iv: float = 0.50) -> List[str]:
        """
        Retorna features con IV sospechosamente alto (posible leakage).

        Args:
            max_iv: Umbral de IV para marcar como sospechoso.

        Returns:
            Lista de features sospechosas.
        """
        return [
            feat for feat, iv in self.iv_values_.items()
            if iv >= max_iv
        ]

    def print_iv_report(self) -> None:
        """Imprime un reporte de IV formateado para consola."""
        summary = self.get_iv_summary()

        print("\n" + "=" * 65)
        print("  SCOREIA -- INFORMATION VALUE (IV) POR FEATURE")
        print("=" * 65)
        print(f"  {'Feature':<30s} {'IV':>8s}   {'Interpretacion'}")
        print("-" * 65)
        for _, row in summary.iterrows():
            marker = ""
            if row["iv"] >= 0.50:
                marker = " (!)"
            elif row["iv"] < 0.02:
                marker = " (x)"
            print(
                f"  {row['feature']:<30s} {row['iv']:>8.4f}   "
                f"{row['interpretacion']}{marker}"
            )
        print("-" * 65)
        n_pred = sum(1 for _, row in summary.iterrows() if row["iv"] >= 0.02)
        print(f"  Predictivas (IV >= 0.02): {n_pred}/{len(summary)}")
        print("=" * 65 + "\n")
