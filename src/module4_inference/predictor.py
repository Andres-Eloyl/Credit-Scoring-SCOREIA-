import logging
from pathlib import Path
from typing import Any, Dict, List, Union

import joblib
import pandas as pd

from src.module4_inference.risk_segmentor import RiskSegmentor

logger = logging.getLogger("SCOREIA.Predictor")

class Predictor:
    """
    Clase para cargar el pipeline serializado de SCOREIA y realizar inferencias
    (predicción de Probabilidad de Incumplimiento y segmento de riesgo) sobre nuevos datos.
    """

    def __init__(self, model_path: str = "models/scoreia_rf_v1.pkl", config_path: str = "config.yaml"):
        """
        Inicializa el Predictor cargando el pipeline de modelo y la configuración de segmentos.

        Args:
            model_path (str): Ruta al archivo .pkl serializado.
            config_path (str): Ruta al archivo config.yaml para los umbrales de riesgo.
        """
        self.model_path = Path(model_path)
        if not self.model_path.exists():
            raise FileNotFoundError(f"No se encontró el modelo serializado en: {self.model_path}")
        
        logger.info(f"Cargando pipeline desde {self.model_path}...")
        self.pipeline_dict = joblib.load(self.model_path)
        
        self.cleaner = self.pipeline_dict["cleaner"]
        self.encoder = self.pipeline_dict["encoder"]
        self.ratios_generator = self.pipeline_dict["ratios_generator"]
        self.selector = self.pipeline_dict["selector"]
        self.model = self.pipeline_dict["model"]
        self.feature_names = self.pipeline_dict["feature_names"]
        
        self.risk_segmentor = RiskSegmentor(config_path=config_path)
        logger.info("Predictor inicializado correctamente.")

    def _preprocess(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Aplica los transformadores del pipeline paso a paso.
        """
        X_clean = self.cleaner.transform(X)
        X_enc = self.encoder.transform(X_clean)
        X_ratios = self.ratios_generator.transform(X_enc)
        X_sel = self.selector.transform(X_ratios)
        return X_sel

    def predict(self, data: Union[Dict[str, Any], pd.DataFrame, List[Dict[str, Any]]]) -> pd.DataFrame:
        """
        Genera la predicción de PD y el segmento de riesgo para uno o varios registros.

        Args:
            data: Puede ser un diccionario (1 registro), una lista de diccionarios, o un DataFrame.

        Returns:
            pd.DataFrame con los datos originales, la PD ('pd') y el segmento de riesgo ('risk_segment').
        """
        if isinstance(data, dict):
            df = pd.DataFrame([data])
        elif isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, pd.DataFrame):
            df = data.copy()
        else:
            raise ValueError("El formato de los datos debe ser dict, list[dict] o pd.DataFrame")
        
        # Guardar copia para devolver con resultados
        df_results = df.copy()
        
        # Preprocesamiento manual del pipeline
        try:
            X_processed = self._preprocess(df)
            
            # Asegurar que el orden de las columnas es el que espera el modelo
            if isinstance(X_processed, pd.DataFrame):
                # Validar que todas las features requeridas están presentes
                missing_features = set(self.feature_names) - set(X_processed.columns)
                if missing_features:
                    raise ValueError(f"Faltan features después del preprocesamiento: {missing_features}")
                
                X_processed = X_processed[self.feature_names]
            
            # Predecir probabilidades (clase 1)
            pd_values = self.model.predict_proba(X_processed)[:, 1]
            
            # Asignar resultados
            df_results["pd"] = pd_values
            df_results["risk_segment"] = df_results["pd"].apply(self.risk_segmentor.segment)
            
            return df_results
            
        except Exception as e:
            logger.error(f"Error durante la inferencia: {str(e)}")
            raise e
