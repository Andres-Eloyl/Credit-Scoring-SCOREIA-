import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import matplotlib.pyplot as plt
import pandas as pd
import shap

from src.module4_inference.predictor import Predictor

logger = logging.getLogger("SCOREIA.Explainability")

class ModelExplainer:
    """
    Clase para proveer explicabilidad individual y global utilizando SHAP.
    Se apoya en la clase Predictor para obtener el modelo y realizar el preprocesamiento de los datos.
    """
    
    def __init__(self, predictor: Predictor, output_dir: str = "reports/decisions"):
        """
        Inicializa el explainer utilizando el estimador de RandomForest dentro del predictor.
        
        Args:
            predictor (Predictor): Instancia del predictor de SCOREIA ya inicializada.
            output_dir (str): Directorio donde se guardarán los gráficos SHAP.
        """
        self.predictor = predictor
        self.model = predictor.model
        self.feature_names = predictor.feature_names
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Inicializar TreeExplainer de SHAP
        logger.info("Inicializando SHAP TreeExplainer...")
        self.explainer = shap.TreeExplainer(self.model)
        logger.info("SHAP TreeExplainer inicializado.")
        
    def _get_shap_explanation(self, X_processed: pd.DataFrame) -> Any:
        """
        Obtiene el objeto Explanation de SHAP. 
        Para RF binario, las explicaciones suelen tener un array de 3D. Seleccionamos la clase 1.
        """
        explanation = self.explainer(X_processed)
        # Para Random Forest en sklearn, explainer() puede devolver un tensor [n_samples, n_features, n_classes]
        # Extraemos solo la clase 1 (incumplimiento)
        if len(explanation.shape) == 3:
            explanation = explanation[:, :, 1]
        return explanation
    
    def explain_individual(self, data: Union[Dict[str, Any], pd.Series, pd.DataFrame], client_id: str) -> None:
        """
        Genera gráficos de explicabilidad individual (Waterfall) para un único cliente
        y los guarda en disco.
        
        Args:
            data: Datos crudos de 1 registro.
            client_id (str): Identificador del cliente (usado para nombrar el archivo).
        """
        if isinstance(data, dict):
            df = pd.DataFrame([data])
        elif isinstance(data, pd.Series):
            df = data.to_frame().T
        elif isinstance(data, pd.DataFrame):
            df = data.copy()
            if len(df) > 1:
                logger.warning("Se pasaron múltiples registros a explain_individual. Se usará el primero.")
                df = df.iloc[[0]]
        else:
            raise ValueError("Formato de datos no soportado.")
            
        # Preprocesar usando el predictor
        X_processed = self.predictor._preprocess(df)
        if isinstance(X_processed, pd.DataFrame):
            X_processed = X_processed[self.feature_names]
            
        # Calcular SHAP values
        explanation = self._get_shap_explanation(X_processed)
        
        # Generar Waterfall plot
        plt.figure(figsize=(10, 6))
        shap.plots.waterfall(explanation[0], show=False)
        plt.title(f"Explicación SHAP (Waterfall) - Cliente: {client_id}")
        plt.tight_layout()
        
        output_path = self.output_dir / f"shap_waterfall_{client_id}.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        logger.info(f"Gráfico Waterfall guardado en {output_path}")

    def explain_global(self, X_df: pd.DataFrame, filename: str = "shap_summary_plot.png") -> None:
        """
        Genera un Summary Plot global utilizando un lote de datos.
        
        Args:
            X_df (pd.DataFrame): Datos crudos del conjunto completo (ej. validación).
            filename (str): Nombre del archivo de salida.
        """
        X_processed = self.predictor._preprocess(X_df)
        if isinstance(X_processed, pd.DataFrame):
            X_processed = X_processed[self.feature_names]
            
        explanation = self._get_shap_explanation(X_processed)
        
        plt.figure(figsize=(12, 8))
        shap.summary_plot(explanation, X_processed, show=False)
        plt.title("Importancia y Efecto Global de las Variables (SHAP)")
        plt.tight_layout()
        
        global_dir = Path("reports/figures")
        global_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = global_dir / filename
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        logger.info(f"Gráfico Summary guardado en {output_path}")
