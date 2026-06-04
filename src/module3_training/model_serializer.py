"""
SCOREIA — Módulo 3: Serializador de Modelos y Artefactos
===========================================================
Responsable de guardar y cargar el pipeline de inferencia completo
y exportar los metadatos de entrenamiento en formato JSON.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import joblib

logger = logging.getLogger("SCOREIA.ModelSerializer")


class ModelSerializer:
    """
    Clase para serializar y deserializar el pipeline de inferencia
    y guardar los metadatos asociados al modelo final de SCOREIA.
    """

    def __init__(self, models_dir: str = "models"):
        """
        Args:
            models_dir: Directorio donde se guardarán los modelos y metadatos.
        """
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)

    def save_pipeline(
        self,
        cleaner: Any,
        encoder: Any,
        ratios_generator: Any,
        selector: Any,
        model: Any,
        feature_names: List[str],
        filename: str = "scoreia_rf_v1.pkl",
    ) -> Path:
        """
        Empaqueta todos los transformadores entrenados y el modelo final
        en un diccionario y los serializa en un único archivo .pkl.

        Args:
            cleaner: Instancia entrenada de DataCleaner.
            encoder: Instancia entrenada de FeatureEncoder.
            ratios_generator: Instancia de RatioGenerator.
            selector: Instancia entrenada de FeatureSelector.
            model: Estimador de RandomForest entrenado y optimizado.
            feature_names: Lista ordenada de features de entrada al modelo.
            filename: Nombre del archivo de salida.

        Returns:
            Ruta al archivo serializado guardado.
        """
        output_path = self.models_dir / filename

        pipeline_dict = {
            "cleaner": cleaner,
            "encoder": encoder,
            "ratios_generator": ratios_generator,
            "selector": selector,
            "model": model,
            "feature_names": feature_names,
            "serialized_at": datetime.now().isoformat(),
        }

        logger.info(f"Guardando pipeline de inferencia en: {output_path}")
        joblib.dump(pipeline_dict, output_path)
        logger.info("Pipeline de inferencia guardado correctamente.")

        return output_path

    def load_pipeline(self, filename: str = "scoreia_rf_v1.pkl") -> Dict[str, Any]:
        """
        Carga el pipeline de inferencia serializado.

        Args:
            filename: Nombre del archivo .pkl a cargar.

        Returns:
            Diccionario con todos los artefactos del pipeline.

        Raises:
            FileNotFoundError: Si el archivo no existe.
        """
        file_path = self.models_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(f"Archivo de modelo no encontrado en: {file_path}")

        logger.info(f"Cargando pipeline de inferencia desde: {file_path}")
        pipeline_dict = joblib.load(file_path)
        return pipeline_dict

    def save_metadata(
        self,
        metrics: Dict[str, float],
        best_params: Dict[str, Any],
        selected_features: List[str],
        config: Dict[str, Any],
        filename: str = "model_metadata.json",
    ) -> Path:
        """
        Guarda los metadatos del modelo en un archivo JSON estructurado.

        Args:
            metrics: Métricas de evaluación obtenidas en test.
            best_params: Hiperparámetros óptimos del modelo.
            selected_features: Lista de features seleccionadas finales.
            config: Configuración del proyecto para documentar umbrales.
            filename: Nombre del archivo JSON de salida.

        Returns:
            Ruta al archivo JSON guardado.
        """
        output_path = self.models_dir / filename

        # Verificar cumplimiento de objetivos
        target_auc = config.get("metrics", {}).get("target_auc_roc", 0.80)
        target_f1 = config.get("metrics", {}).get("target_f1_score", 0.72)

        auc_met = metrics.get("auc_roc", 0.0) >= target_auc
        f1_met = metrics.get("f1_score", 0.0) >= target_f1

        metadata = {
            "project_name": config.get("project", {}).get("name", "SCOREIA"),
            "model_version": config.get("project", {}).get("version", "1.0.0"),
            "algorithm": config.get("training", {}).get("model", "RandomForestClassifier"),
            "trained_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "environment": {
                "python_version": config.get("project", {}).get("python_version", "3.11"),
            },
            "best_hyperparameters": best_params,
            "metrics": {k: round(v, 6) for k, v in metrics.items()},
            "targets": {
                "target_auc_roc": target_auc,
                "target_f1_score": target_f1,
            },
            "objectives_met": {
                "auc_roc": bool(auc_met),
                "f1_score": bool(f1_met),
                "all_met": bool(auc_met and f1_met),
            },
            "features": {
                "n_selected": len(selected_features),
                "selected_list": selected_features,
            },
        }

        logger.info(f"Guardando metadatos del modelo en: {output_path}")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=4, ensure_ascii=False)
        logger.info("Metadatos del modelo guardados correctamente.")

        return output_path
