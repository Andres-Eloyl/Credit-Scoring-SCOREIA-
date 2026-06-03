"""
SCOREIA — Módulo 1: DataLoader
================================
Carga y validación de datos crudos desde CSV/Excel.
Valida esquema, tipos de datos y formato antes de pasar al pipeline.

Responsabilidades:
  - Lectura de archivos CSV y Excel
  - Validación del esquema esperado (16 features + 1 label)
  - Reporte de calidad inicial (nulos, duplicados, tipos)
  - Conversión de tipos de datos al esquema SCOREIA

Uso:
    from module1_preprocessing.data_loader import DataLoader
    loader = DataLoader(config_path="config.yaml")
    df = loader.load("data/raw/credit_data_synthetic.csv")
"""

import logging
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import yaml

logger = logging.getLogger("SCOREIA.DataLoader")


# =============================================================================
# ESQUEMA ESPERADO DE SCOREIA
# =============================================================================

SCOREIA_SCHEMA = {
    # F01–F16: Features predictoras
    "edad":                 "int",
    "estado_civil":         "category",
    "nivel_educativo":      "category",
    "tipo_vivienda":        "category",
    "ingreso_mensual":      "float",
    "antiguedad_laboral":   "float",     # float por posibles NaN
    "tipo_contrato":        "category",
    "score_buro":           "float",     # float por posibles NaN
    "meses_mora_maxima":    "float",     # float por posibles NaN
    "num_creditos_activos": "int",
    "consultas_buro_6m":    "float",     # float por posibles NaN
    "ratio_deuda_ingreso":  "float",
    "utilizacion_credito":  "float",     # float por posibles NaN
    "monto_solicitado":     "float",
    "plazo_meses":          "int",
    "tipo_prestamo":        "category",
    # Label
    "incumplimiento":       "int",
}

EXPECTED_COLUMNS = list(SCOREIA_SCHEMA.keys())

CATEGORICAL_COLUMNS = [
    "estado_civil", "nivel_educativo", "tipo_vivienda",
    "tipo_contrato", "tipo_prestamo",
]

NUMERICAL_COLUMNS = [
    "edad", "ingreso_mensual", "antiguedad_laboral", "score_buro",
    "meses_mora_maxima", "num_creditos_activos", "consultas_buro_6m",
    "ratio_deuda_ingreso", "utilizacion_credito", "monto_solicitado",
    "plazo_meses",
]

LABEL_COLUMN = "incumplimiento"


# =============================================================================
# EXPECTED CATEGORY VALUES
# =============================================================================

EXPECTED_CATEGORIES = {
    "estado_civil":    ["Soltero", "Casado", "Divorciado", "Viudo"],
    "nivel_educativo": ["Primaria", "Secundaria", "Universidad", "Posgrado"],
    "tipo_vivienda":   ["Propia", "Arrendada", "Familiar"],
    "tipo_contrato":   ["Indefinido", "Temporal", "Independiente"],
    "tipo_prestamo":   ["Personal", "Hipotecario", "Automotriz", "Tarjeta"],
}


# =============================================================================
# CLASE DataLoader
# =============================================================================

class DataLoader:
    """
    Carga y valida datos crudos según el esquema de SCOREIA.

    Attributes:
        config: Diccionario de configuración cargado desde config.yaml.
        validation_report: Diccionario con resultados de la última validación.
    """

    def __init__(self, config_path: str = "config.yaml"):
        """
        Args:
            config_path: Ruta al archivo de configuración YAML.
        """
        self.config = self._load_config(config_path)
        self.validation_report: dict = {}

    @staticmethod
    def _load_config(config_path: str) -> dict:
        """Carga la configuración YAML del proyecto."""
        config_file = Path(config_path)
        if not config_file.exists():
            logger.warning(
                f"Archivo de configuración '{config_path}' no encontrado. "
                "Usando valores por defecto."
            )
            return {}

        with open(config_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def load(
        self,
        filepath: str,
        validate: bool = True,
        verbose: bool = True,
    ) -> pd.DataFrame:
        """
        Carga un archivo de datos y opcionalmente valida su esquema.

        Args:
            filepath: Ruta al archivo CSV o Excel.
            validate: Si True, ejecuta validación del esquema completo.
            verbose: Si True, imprime reporte de calidad.

        Returns:
            DataFrame con los datos cargados y tipos corregidos.

        Raises:
            FileNotFoundError: Si el archivo no existe.
            ValueError: Si el esquema no es válido (columnas faltantes).
        """
        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {filepath}")

        # ── Leer según extensión ───────────────────────────────────────
        logger.info(f"Cargando datos desde: {filepath}")
        if filepath.suffix.lower() == ".csv":
            df = pd.read_csv(filepath)
        elif filepath.suffix.lower() in (".xls", ".xlsx"):
            df = pd.read_excel(filepath)
        else:
            raise ValueError(
                f"Formato no soportado: {filepath.suffix}. "
                "Use CSV (.csv) o Excel (.xls, .xlsx)."
            )

        logger.info(f"Datos cargados: {df.shape[0]:,} filas x {df.shape[1]} columnas")

        # ── Validación ──────────────────────────────────────────────────
        if validate:
            self._validate_schema(df)
            df = self._cast_types(df)

        # ── Reporte de calidad ──────────────────────────────────────────
        self.validation_report = self._generate_quality_report(df)
        if verbose:
            self._print_quality_report()

        return df

    def _validate_schema(self, df: pd.DataFrame) -> None:
        """
        Valida que el DataFrame contenga exactamente las columnas esperadas.

        Raises:
            ValueError: Si hay columnas faltantes o desconocidas.
        """
        actual_cols = set(df.columns)
        expected_cols = set(EXPECTED_COLUMNS)

        missing = expected_cols - actual_cols
        extra = actual_cols - expected_cols

        if missing:
            raise ValueError(
                f"Columnas faltantes en el dataset: {sorted(missing)}. "
                f"El esquema SCOREIA requiere exactamente {len(EXPECTED_COLUMNS)} columnas."
            )

        if extra:
            logger.warning(
                f"Columnas adicionales encontradas (serán ignoradas): {sorted(extra)}"
            )

        # Validar categorías válidas
        for col, valid_values in EXPECTED_CATEGORIES.items():
            if col in df.columns:
                unique_vals = set(df[col].dropna().unique())
                invalid = unique_vals - set(valid_values)
                if invalid:
                    logger.warning(
                        f"Valores inesperados en '{col}': {invalid}. "
                        f"Valores válidos: {valid_values}"
                    )

        # Validar que el label es binario
        if LABEL_COLUMN in df.columns:
            unique_labels = set(df[LABEL_COLUMN].dropna().unique())
            if not unique_labels.issubset({0, 1}):
                raise ValueError(
                    f"La variable '{LABEL_COLUMN}' debe ser binaria (0/1). "
                    f"Valores encontrados: {unique_labels}"
                )

        logger.info("Validacion de esquema completada exitosamente.")

    @staticmethod
    def _cast_types(df: pd.DataFrame) -> pd.DataFrame:
        """
        Convierte los tipos de datos al esquema esperado de SCOREIA.
        Las columnas con NaN se mantienen como float (int no soporta NaN nativo).
        """
        df = df.copy()

        for col in CATEGORICAL_COLUMNS:
            if col in df.columns:
                df[col] = df[col].astype("category")

        # Numéricas enteras sin NaN → int
        for col in ["edad", "num_creditos_activos", "plazo_meses", LABEL_COLUMN]:
            if col in df.columns and df[col].notna().all():
                df[col] = df[col].astype(int)

        # Numéricas float (pueden tener NaN)
        float_cols = [
            "ingreso_mensual", "antiguedad_laboral", "score_buro",
            "meses_mora_maxima", "consultas_buro_6m", "ratio_deuda_ingreso",
            "utilizacion_credito", "monto_solicitado",
        ]
        for col in float_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        return df

    def _generate_quality_report(self, df: pd.DataFrame) -> dict:
        """
        Genera un reporte de calidad de datos.

        Returns:
            Diccionario con métricas de calidad.
        """
        total_cells = df.shape[0] * df.shape[1]
        total_nulls = df.isnull().sum().sum()

        report = {
            "n_rows": df.shape[0],
            "n_columns": df.shape[1],
            "total_cells": total_cells,
            "total_nulls": int(total_nulls),
            "null_percentage": round(total_nulls / total_cells * 100, 2),
            "n_duplicates": int(df.duplicated().sum()),
            "null_per_column": df.isnull().sum().to_dict(),
            "dtypes": df.dtypes.astype(str).to_dict(),
            "class_distribution": (
                df[LABEL_COLUMN].value_counts(normalize=True).to_dict()
                if LABEL_COLUMN in df.columns
                else {}
            ),
        }
        return report

    def _print_quality_report(self) -> None:
        """Imprime el reporte de calidad de datos en formato legible."""
        r = self.validation_report
        if not r:
            return

        print("\n" + "=" * 60)
        print("  SCOREIA -- REPORTE DE CALIDAD DE DATOS")
        print("=" * 60)
        print(f"  Filas totales       : {r['n_rows']:>10,}")
        print(f"  Columnas            : {r['n_columns']:>10}")
        print(f"  Celdas totales      : {r['total_cells']:>10,}")
        print(f"  Valores nulos       : {r['total_nulls']:>10,}  ({r['null_percentage']:.2f}%)")
        print(f"  Filas duplicadas    : {r['n_duplicates']:>10,}")
        print("=" * 60)

        # Nulos por columna (solo las que tienen nulos)
        cols_with_nulls = {
            k: v for k, v in r["null_per_column"].items() if v > 0
        }
        if cols_with_nulls:
            print("\n-- Columnas con valores nulos --------------------------")
            for col, count in sorted(cols_with_nulls.items(), key=lambda x: -x[1]):
                pct = count / r["n_rows"] * 100
                print(f"  {col:<25s}: {count:>5,}  ({pct:.1f}%)")

        # Distribución de clases
        if r["class_distribution"]:
            print("\n-- Distribucion de clases (incumplimiento) -------------")
            for label, pct in sorted(r["class_distribution"].items()):
                label_name = "Pago" if label == 0 else "Incumplimiento"
                print(f"  {label} ({label_name:<15s}): {pct:.1%}")

        print()
