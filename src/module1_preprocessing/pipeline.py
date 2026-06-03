"""
SCOREIA — Módulo 1: Pipeline de Preprocesamiento
====================================================
Orquestador que encadena todos los pasos de preprocesamiento en un
pipeline reproducible y libre de data leakage.

Flujo del pipeline:
  1. Cargar datos crudos (DataLoader)
  2. Dividir train/test ESTRATIFICADO (antes de cualquier transformación)
  3. Ajustar limpieza sobre train → aplicar a ambos (DataCleaner)
  4. Ajustar encoding sobre train → aplicar a ambos (FeatureEncoder)
  5. Aplicar SMOTE solo sobre train (ClassBalancer)
  6. Guardar datos procesados en data/processed/

PRINCIPIO ANTI-LEAKAGE:
  - Split ANTES de fit
  - fit() SOLO sobre train
  - transform() sobre train y test
  - SMOTE SOLO sobre train

Uso:
    from module1_preprocessing.pipeline import PreprocessingPipeline
    pipeline = PreprocessingPipeline(config_path="config.yaml")
    result = pipeline.run(filepath="data/raw/credit_data_synthetic.csv")
"""

import logging
import json
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import pandas as pd
import yaml
from sklearn.model_selection import train_test_split

from .data_loader import DataLoader, LABEL_COLUMN, NUMERICAL_COLUMNS, CATEGORICAL_COLUMNS
from .cleaner import DataCleaner
from .encoder import FeatureEncoder
from .balancer import ClassBalancer

logger = logging.getLogger("SCOREIA.Pipeline")


class PreprocessingResult:
    """
    Contenedor de resultados del pipeline de preprocesamiento.
    Almacena todos los artefactos para uso posterior.
    """

    def __init__(self):
        self.X_train: Optional[pd.DataFrame] = None
        self.X_test: Optional[pd.DataFrame] = None
        self.y_train: Optional[pd.Series] = None
        self.y_test: Optional[pd.Series] = None
        self.X_train_balanced: Optional[pd.DataFrame] = None
        self.y_train_balanced: Optional[pd.Series] = None
        self.cleaner: Optional[DataCleaner] = None
        self.encoder: Optional[FeatureEncoder] = None
        self.balancer: Optional[ClassBalancer] = None
        self.quality_report: dict = {}
        self.pipeline_summary: dict = {}


class PreprocessingPipeline:
    """
    Pipeline completo de preprocesamiento para SCOREIA.

    Encadena DataLoader → Split → DataCleaner → FeatureEncoder → SMOTE
    garantizando que NO hay data leakage en ningún paso.

    Attributes:
        config (dict): Configuración cargada desde config.yaml.
        loader (DataLoader): Instancia del cargador de datos.
        cleaner (DataCleaner): Instancia del limpiador.
        encoder (FeatureEncoder): Instancia del codificador.
        balancer (ClassBalancer): Instancia del balanceador.
    """

    def __init__(self, config_path: str = "config.yaml"):
        """
        Args:
            config_path: Ruta al archivo de configuración YAML.
        """
        self.config = self._load_config(config_path)
        self.config_path = config_path

        # Extraer configuraciones
        preproc_cfg = self.config.get("preprocessing", {})
        smote_cfg = preproc_cfg.get("smote", {})
        project_cfg = self.config.get("project", {})

        self.test_size = preproc_cfg.get("test_size", 0.20)
        self.random_seed = project_cfg.get("random_seed", 42)
        self.iqr_multiplier = preproc_cfg.get("outlier_iqr_multiplier", 1.5)

        # Inicializar componentes
        self.loader = DataLoader(config_path=config_path)
        self.cleaner = DataCleaner(
            iqr_multiplier=self.iqr_multiplier,
            numerical_strategy=preproc_cfg.get("numerical_imputer_strategy", "median"),
            categorical_strategy=preproc_cfg.get("categorical_imputer_strategy", "most_frequent"),
        )
        self.encoder = FeatureEncoder()
        self.balancer = ClassBalancer(
            method="smote",
            sampling_strategy=smote_cfg.get("sampling_strategy", "minority"),
            k_neighbors=smote_cfg.get("k_neighbors", 5),
            random_state=smote_cfg.get("random_state", self.random_seed),
        )

    @staticmethod
    def _load_config(config_path: str) -> dict:
        """Carga la configuración YAML."""
        path = Path(config_path)
        if not path.exists():
            logger.warning(f"Config '{config_path}' no encontrado. Usando defaults.")
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def run(
        self,
        filepath: str,
        save_processed: bool = True,
        output_dir: str = "data/processed",
        apply_smote: bool = True,
        verbose: bool = True,
    ) -> PreprocessingResult:
        """
        Ejecuta el pipeline completo de preprocesamiento.

        Args:
            filepath: Ruta al archivo CSV con datos crudos.
            save_processed: Si True, guarda los datos procesados en disco.
            output_dir: Directorio de salida para datos procesados.
            apply_smote: Si True, aplica SMOTE sobre el train set.
            verbose: Si True, imprime resúmenes en cada paso.

        Returns:
            PreprocessingResult con todos los artefactos del pipeline.
        """
        result = PreprocessingResult()

        logger.info("=" * 60)
        logger.info("  SCOREIA -- PIPELINE DE PREPROCESAMIENTO")
        logger.info("=" * 60)

        # ═══════════════════════════════════════════════════════════════
        # PASO 1: CARGAR DATOS CRUDOS
        # ═══════════════════════════════════════════════════════════════
        logger.info("[PASO 1/5] Cargando datos crudos...")
        df = self.loader.load(filepath, validate=True, verbose=verbose)
        result.quality_report = self.loader.validation_report

        # ═══════════════════════════════════════════════════════════════
        # PASO 2: SPLIT TRAIN/TEST ESTRATIFICADO
        # ═══════════════════════════════════════════════════════════════
        logger.info(
            f"[PASO 2/5] Dividiendo datos: train={1-self.test_size:.0%} / "
            f"test={self.test_size:.0%} (estratificado)..."
        )
        X = df.drop(columns=[LABEL_COLUMN])
        y = df[LABEL_COLUMN]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=self.test_size,
            random_state=self.random_seed,
            stratify=y,
        )

        logger.info(
            f"  Train: {len(X_train):,} muestras | "
            f"Test: {len(X_test):,} muestras"
        )
        logger.info(
            f"  Train label dist: {y_train.value_counts().to_dict()} | "
            f"Test label dist: {y_test.value_counts().to_dict()}"
        )

        # ═══════════════════════════════════════════════════════════════
        # PASO 3: LIMPIEZA (fit en train, transform en ambos)
        # ═══════════════════════════════════════════════════════════════
        logger.info("[PASO 3/5] Limpieza: imputacion + capping de outliers...")

        self.cleaner.fit(X_train)
        X_train_clean = self.cleaner.transform(X_train)
        X_test_clean = self.cleaner.transform(X_test)

        if verbose:
            summary = self.cleaner.get_cleaning_summary()
            n_rules = len(summary["imputation_rules"])
            n_cap = len(summary["capping_rules"])
            logger.info(
                f"  Limpieza aplicada: {n_rules} reglas de imputacion, "
                f"{n_cap} reglas de capping"
            )

        # ═══════════════════════════════════════════════════════════════
        # PASO 4: ENCODING (fit en train, transform en ambos)
        # ═══════════════════════════════════════════════════════════════
        logger.info("[PASO 4/5] Encoding: OHE + ordinal...")

        self.encoder.fit(X_train_clean)
        X_train_encoded = self.encoder.transform(X_train_clean)
        X_test_encoded = self.encoder.transform(X_test_clean)

        logger.info(
            f"  Features antes del encoding: {X_train_clean.shape[1]} | "
            f"despues: {X_train_encoded.shape[1]}"
        )

        # Guardar versiones sin SMOTE
        result.X_train = X_train_encoded
        result.X_test = X_test_encoded
        result.y_train = y_train.reset_index(drop=True)
        result.y_test = y_test.reset_index(drop=True)

        # Reset indices para consistencia
        result.X_train = result.X_train.reset_index(drop=True)
        result.X_test = result.X_test.reset_index(drop=True)

        # ═══════════════════════════════════════════════════════════════
        # PASO 5: SMOTE (solo sobre train)
        # ═══════════════════════════════════════════════════════════════
        if apply_smote:
            logger.info(
                "[PASO 5/5] SMOTE: generando muestras sinteticas "
                "(SOLO en train set)..."
            )
            X_train_balanced, y_train_balanced = self.balancer.fit_resample(
                result.X_train, result.y_train
            )
            result.X_train_balanced = X_train_balanced
            result.y_train_balanced = y_train_balanced
        else:
            logger.info("[PASO 5/5] SMOTE desactivado — sin balanceo.")
            result.X_train_balanced = result.X_train.copy()
            result.y_train_balanced = result.y_train.copy()

        # ═══════════════════════════════════════════════════════════════
        # GUARDAR ARTEFACTOS
        # ═══════════════════════════════════════════════════════════════
        result.cleaner = self.cleaner
        result.encoder = self.encoder
        result.balancer = self.balancer

        # Generar resumen del pipeline
        result.pipeline_summary = self._build_summary(result)

        if save_processed:
            self._save_processed_data(result, output_dir)

        if verbose:
            self._print_summary(result)

        logger.info("Pipeline de preprocesamiento completado exitosamente.")
        return result

    def _build_summary(self, result: PreprocessingResult) -> dict:
        """Construye un resumen completo del pipeline."""
        return {
            "input_shape": {
                "rows": result.X_train.shape[0] + result.X_test.shape[0],
                "features_original": len(NUMERICAL_COLUMNS) + len(CATEGORICAL_COLUMNS),
            },
            "split": {
                "train_size": result.X_train.shape[0],
                "test_size": result.X_test.shape[0],
                "test_ratio": self.test_size,
            },
            "cleaning": self.cleaner.get_cleaning_summary(),
            "encoding": {
                "features_after_encoding": result.X_train.shape[1],
                "ohe_columns": list(self.encoder.ohe_categories_.keys()),
                "ordinal_columns": list(self.encoder.ordinal_mapping.keys()),
            },
            "balancing": (
                self.balancer.get_balancing_summary()
                if result.X_train_balanced is not None
                else {}
            ),
            "output_shapes": {
                "X_train": list(result.X_train.shape),
                "X_test": list(result.X_test.shape),
                "X_train_balanced": (
                    list(result.X_train_balanced.shape)
                    if result.X_train_balanced is not None
                    else None
                ),
            },
        }

    def _save_processed_data(
        self,
        result: PreprocessingResult,
        output_dir: str,
    ) -> None:
        """Guarda los datos procesados en disco como parquet."""
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        # Guardar train (sin SMOTE) y test como parquet
        train_df = pd.concat(
            [result.X_train, result.y_train.rename(LABEL_COLUMN)],
            axis=1,
        )
        test_df = pd.concat(
            [result.X_test, result.y_test.rename(LABEL_COLUMN)],
            axis=1,
        )

        train_path = out_path / "train_processed.csv"
        test_path = out_path / "test_processed.csv"

        train_df.to_csv(train_path, index=False)
        test_df.to_csv(test_path, index=False)

        logger.info(f"Train procesado guardado en: {train_path}")
        logger.info(f"Test procesado guardado en: {test_path}")

        # Guardar train balanceado
        if result.X_train_balanced is not None:
            balanced_df = pd.concat(
                [
                    result.X_train_balanced,
                    result.y_train_balanced.rename(LABEL_COLUMN),
                ],
                axis=1,
            )
            balanced_path = out_path / "train_balanced.csv"
            balanced_df.to_csv(balanced_path, index=False)
            logger.info(f"Train balanceado guardado en: {balanced_path}")

        # Guardar resumen como JSON
        summary_path = out_path / "pipeline_summary.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(
                result.pipeline_summary, f,
                indent=2, ensure_ascii=False, default=str,
            )
        logger.info(f"Resumen del pipeline guardado en: {summary_path}")

    @staticmethod
    def _print_summary(result: PreprocessingResult) -> None:
        """Imprime un resumen del pipeline ejecutado."""
        s = result.pipeline_summary

        print("\n" + "=" * 60)
        print("  SCOREIA -- RESUMEN DEL PIPELINE DE PREPROCESAMIENTO")
        print("=" * 60)

        # Split
        split = s.get("split", {})
        print(f"\n  [SPLIT]")
        print(f"    Train : {split.get('train_size', '?'):>8,} muestras")
        print(f"    Test  : {split.get('test_size', '?'):>8,} muestras")

        # Encoding
        enc = s.get("encoding", {})
        print(f"\n  [ENCODING]")
        print(f"    Features tras encoding : {enc.get('features_after_encoding', '?')}")
        print(f"    OHE columns            : {enc.get('ohe_columns', [])}")
        print(f"    Ordinal columns        : {enc.get('ordinal_columns', [])}")

        # Balanceo
        bal = s.get("balancing", {})
        if bal:
            print(f"\n  [SMOTE]")
            print(f"    Metodo              : {bal.get('method', '?').upper()}")
            print(f"    Antes               : {bal.get('before', {})}")
            print(f"    Despues             : {bal.get('after', {})}")
            print(f"    Muestras sinteticas : +{bal.get('n_synthetic', 0):,}")

        # Output shapes
        shapes = s.get("output_shapes", {})
        print(f"\n  [OUTPUT]")
        print(f"    X_train          : {shapes.get('X_train', '?')}")
        print(f"    X_test           : {shapes.get('X_test', '?')}")
        print(f"    X_train_balanced : {shapes.get('X_train_balanced', '?')}")

        print("\n" + "=" * 60)
        print()
