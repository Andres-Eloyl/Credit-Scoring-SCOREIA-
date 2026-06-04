"""
SCOREIA — Módulo 3: Orquestador de Entrenamiento
===================================================
Coordina la ejecución de la Fase 3: carga datos preprocesados, realiza la
ingeniería de variables y la selección de features, ejecuta RandomizedSearchCV
sobre RandomForest con validación cruzada estratificada, evalúa en test,
serializa el pipeline de inferencia completo y registra en MLflow.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
import yaml
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import RandomizedSearchCV

import mlflow
import mlflow.sklearn

from src.module1_preprocessing.pipeline import PreprocessingPipeline
from src.module2_features.feature_selector import FeatureSelector
from src.module2_features.ratios import RatioGenerator
from .evaluator import SCOREIAEvaluator
from .model_serializer import ModelSerializer

logger = logging.getLogger("SCOREIA.Trainer")


class SCOREIATrainer:
    """
    Clase principal para entrenar, optimizar, evaluar y serializar
    el modelo de RandomForestClassifier en el sistema SCOREIA.
    """

    def __init__(self, config_path: str = "config.yaml"):
        """
        Args:
            config_path: Ruta al archivo config.yaml central.
        """
        self.config_path = config_path
        self.config = self._load_config(config_path)

        # Cargar variables de configuración
        project_cfg = self.config.get("project", {})
        train_cfg = self.config.get("training", {})
        paths_cfg = self.config.get("paths", {})

        self.random_seed = project_cfg.get("random_seed", 42)
        self.cv_folds = train_cfg.get("cv_folds", 5)
        self.cv_scoring = train_cfg.get("cv_scoring", "roc_auc")
        self.n_iter = train_cfg.get("n_iter_search", 50)
        self.n_jobs = train_cfg.get("n_jobs", -1)

        # Rutas
        self.raw_data_dir = Path(paths_cfg.get("data_raw", "data/raw/"))
        self.models_dir = Path(paths_cfg.get("models", "models/"))
        self.reports_dir = Path(paths_cfg.get("reports", "reports/"))
        self.figures_dir = Path(paths_cfg.get("reports_figures", "reports/figures/"))

        # Archivo de datos crudos sintéticos
        synthetic_cfg = self.config.get("synthetic_data", {})
        self.data_filepath = self.raw_data_dir / synthetic_cfg.get(
            "output_filename", "credit_data_synthetic.csv"
        )

        # Nombre de archivos de salida
        self.model_filename = train_cfg.get("model_filename", "scoreia_rf_v1.pkl")
        self.metadata_filename = train_cfg.get("metadata_filename", "model_metadata.json")

    @staticmethod
    def _load_config(config_path: str) -> dict:
        """Carga el archivo de configuración YAML."""
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def run(self) -> Dict[str, Any]:
        """
        Ejecuta el flujo completo de entrenamiento del modelo SCOREIA.

        Flujo:
          1. Inicializar experimento MLflow.
          2. Ejecutar PreprocessingPipeline (Load, Clean, Encode, SMOTE).
          3. Aplicar Ingeniería de Variables (RatioGenerator).
          4. Ajustar y aplicar Selección de Features (FeatureSelector).
          5. Búsqueda de Hiperparámetros (RandomizedSearchCV con RF).
          6. Evaluación de desempeño en test (SCOREIAEvaluator).
          7. Serializar pipeline completo y metadatos (ModelSerializer).
          8. Registrar en MLflow.

        Returns:
            Diccionario de resultados que contiene métricas del modelo entrenado.
        """
        logger.info("Iniciando pipeline de entrenamiento SCOREIA...")

        # ── 1. Configurar MLflow ───────────────────────────────────────
        mlflow.set_experiment("SCOREIA-Training")
        
        # Iniciar corrida de MLflow
        with mlflow.start_run(run_name="RandomForest_Optimization") as run:
            run_id = run.info.run_id
            logger.info(f"Corrida de MLflow iniciada con ID: {run_id}")

            # Registrar parámetros globales de configuración
            mlflow.log_params({
                "cv_folds": self.cv_folds,
                "cv_scoring": self.cv_scoring,
                "n_iter_search": self.n_iter,
                "random_seed": self.random_seed,
            })

            # ── 2. Preprocesamiento (Módulo 1) ──────────────────────────
            logger.info("Fase Preprocesamiento (Módulo 1)...")
            preproc_pipeline = PreprocessingPipeline(config_path=self.config_path)
            
            # Comprobar existencia del archivo de entrada
            if not self.data_filepath.exists():
                raise FileNotFoundError(
                    f"El dataset crudo sintético no se encuentra en {self.data_filepath}. "
                    "Por favor genere los datos antes de entrenar."
                )

            # Ejecutar preprocesamiento (SMOTE activado para entrenamiento)
            preproc_res = preproc_pipeline.run(
                filepath=str(self.data_filepath),
                save_processed=True,
                apply_smote=True,
                verbose=False
            )

            X_train = preproc_res.X_train_balanced
            y_train = preproc_res.y_train_balanced
            X_test = preproc_res.X_test
            y_test = preproc_res.y_test

            logger.info(f"  Datos de entrenamiento (SMOTE): {X_train.shape}")
            logger.info(f"  Datos de prueba (Crudos): {X_test.shape}")

            # ── 3. Ingeniería de Variables (Módulo 2: Ratios) ───────────
            logger.info("Generación de ratios financieros (Módulo 2)...")
            ratio_gen = RatioGenerator()
            ratio_gen.fit(X_train)
            X_train_ratios = ratio_gen.transform(X_train)
            X_test_ratios = ratio_gen.transform(X_test)

            # ── 4. Selección de Features (Módulo 2: Selector) ───────────
            logger.info("Selección de características por IV y correlación (Módulo 2)...")
            preproc_cfg = self.config.get("preprocessing", {})
            fe_cfg = self.config.get("feature_engineering", {})
            woe_cfg = fe_cfg.get("woe", {})

            # Obtener variables categóricas finales tras OHE
            # Estas variables NO deben recibir WoE binning porque ya fueron transformadas en OHE
            # pero necesitamos saber qué columnas numéricas filtrar. El FeatureSelector auto-detecta esto.
            selector = FeatureSelector(
                min_iv=woe_cfg.get("min_iv_threshold", 0.02),
                max_correlation=0.85,  # Basado en el diseño
                min_variance=0.001,
                n_bins_woe=woe_cfg.get("max_bins", 10),
            )

            selector.fit(X_train_ratios, y_train)
            X_train_final = selector.transform(X_train_ratios)
            X_test_final = selector.transform(X_test_ratios)

            logger.info(f"  Features finales seleccionadas: {X_train_final.shape[1]}/{X_train_ratios.shape[1]}")
            logger.info(f"  Lista de features: {list(X_train_final.columns)}")

            # Registrar el reporte de selección de features como texto/csv en mlflow
            report_df = selector.get_selection_report()
            report_csv_path = self.reports_dir / "feature_selection_report.csv"
            report_df.to_csv(report_csv_path, index=False)
            mlflow.log_artifact(str(report_csv_path), artifact_path="reports")

            # ── 5. Búsqueda de Hiperparámetros (Módulo 3) ──────────────
            logger.info("Búsqueda de hiperparámetros RandomForest...")
            train_cfg = self.config.get("training", {})
            param_space = train_cfg.get("hyperparameter_space", {})

            # Instanciar modelo base
            rf_base = RandomForestClassifier(random_state=self.random_seed)

            # Configurar la búsqueda aleatoria con validación cruzada estratificada
            search = RandomizedSearchCV(
                estimator=rf_base,
                param_distributions=param_space,
                n_iter=self.n_iter,
                scoring=self.cv_scoring,
                cv=self.cv_folds,
                random_state=self.random_seed,
                n_jobs=self.n_jobs,
                verbose=1,
                refit=True
            )

            logger.info(
                f"Ejecutando RandomizedSearchCV ({self.n_iter} iteraciones, "
                f"CV={self.cv_folds} folds)..."
            )
            search.fit(X_train_final, y_train)

            best_rf = search.best_estimator_
            best_params = search.best_params_
            best_cv_score = search.best_score_

            logger.info(f"  Mejor score de CV ({self.cv_scoring}): {best_cv_score:.4f}")
            logger.info(f"  Mejores hiperparámetros: {best_params}")

            # Registrar los mejores hiperparámetros del modelo en mlflow
            # Si un hiperparámetro es None, convertirlo a string para evitar errores en mlflow
            logged_params = {k: (str(v) if v is None else v) for k, v in best_params.items()}
            mlflow.log_params(logged_params)
            mlflow.log_metric(f"best_cv_{self.cv_scoring}", best_cv_score)

            # ── 6. Evaluación (Módulo 3: Evaluator) ────────────────────
            evaluator = SCOREIAEvaluator(config=self.config)
            metrics = evaluator.evaluate(best_rf, X_test_final, y_test)
            
            # Generar y guardar curvas (ROC, PR, ConfMat)
            evaluator.plot_curves(best_rf, X_test_final, y_test, output_dir=str(self.figures_dir))
            
            # Imprimir reporte formal por consola
            evaluator.print_report()

            # Registrar métricas en MLflow
            mlflow.log_metrics({
                "test_auc_roc": metrics["auc_roc"],
                "test_f1_score": metrics["f1_score"],
                "test_precision": metrics["precision"],
                "test_recall": metrics["recall"],
                "test_accuracy": metrics["accuracy"],
            })

            # Registrar curvas generadas en MLflow
            for fig_file in self.figures_dir.glob("*.png"):
                mlflow.log_artifact(str(fig_file), artifact_path="plots")

            # ── 7. Serialización (Módulo 3: Serializer) ─────────────────
            serializer = ModelSerializer(models_dir=str(self.models_dir))
            
            # Guardar pipeline de transformación completo + clasificador
            model_path = serializer.save_pipeline(
                cleaner=preproc_res.cleaner,
                encoder=preproc_res.encoder,
                ratios_generator=ratio_gen,
                selector=selector,
                model=best_rf,
                feature_names=list(X_train_final.columns),
                filename=self.model_filename
            )

            # Guardar metadatos JSON
            metadata_path = serializer.save_metadata(
                metrics=metrics,
                best_params=best_params,
                selected_features=list(X_train_final.columns),
                config=self.config,
                filename=self.metadata_filename
            )

            # Registrar artefactos del modelo en MLflow
            mlflow.log_artifact(str(model_path), artifact_path="model_package")
            mlflow.log_artifact(str(metadata_path), artifact_path="model_package")
            
            # Registrar el modelo formalmente en MLflow
            mlflow.sklearn.log_model(
                sk_model=best_rf,
                artifact_path="model",
                registered_model_name="SCOREIA_RandomForest"
            )

            # Reportar finalización exitosa
            logger.info("Pipeline de entrenamiento completado exitosamente.")
            
            # Validar objetivos del proyecto
            target_auc = self.config.get("metrics", {}).get("target_auc_roc", 0.80)
            target_f1 = self.config.get("metrics", {}).get("target_f1_score", 0.72)
            
            auc_ok = metrics["auc_roc"] >= target_auc
            f1_ok = metrics.get("opt_f1_score", metrics["f1_score"]) >= target_f1
            
            if auc_ok and f1_ok:
                logger.info("[EXITO] ¡SE CUMPLIERON TODOS LOS OBJETIVOS DEL PROYECTO!")
            else:
                logger.warning(
                    f"[ALERTA] No se alcanzaron todos los objetivos. "
                    f"AUC: {metrics['auc_roc']:.4f}/{target_auc} | "
                    f"F1 (Opt): {metrics.get('opt_f1_score', metrics['f1_score']):.4f}/{target_f1}"
                )

            return {
                "metrics": metrics,
                "best_params": best_params,
                "run_id": run_id,
                "objectives_met": bool(auc_ok and f1_ok)
            }
