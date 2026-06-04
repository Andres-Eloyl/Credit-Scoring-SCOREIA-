import logging
import pandas as pd
from pathlib import Path
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset

logger = logging.getLogger("SCOREIA.DriftDetector")

class DriftDetector:
    """
    Clase para detectar Data Drift (cambio en la distribución de los datos de entrada)
    utilizando la librería Evidently.
    """
    def __init__(self, config_path: str = "config.yaml"):
        import yaml
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
            
        self.monitoring_config = self.config.get("monitoring", {})
        self.drift_threshold = self.monitoring_config.get("drift_threshold", 0.05)
        
        self.output_dir = Path("reports/monitoring")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_report(self, reference_data: pd.DataFrame, current_data: pd.DataFrame, filename: str = "data_drift_report.html") -> bool:
        """
        Genera un reporte de drift comparando los datos de referencia (entrenamiento)
        con los datos actuales (producción o nueva muestra).
        
        Args:
            reference_data (pd.DataFrame): Datos de referencia.
            current_data (pd.DataFrame): Nuevos datos a evaluar.
            filename (str): Nombre del archivo HTML de salida.
            
        Returns:
            bool: True si se detecta drift en el dataset, False en caso contrario.
        """
        logger.info("Generando reporte de Data Drift con Evidently...")
        
        data_drift_report = Report(metrics=[
            DataDriftPreset(stattest_threshold=self.drift_threshold),
        ])
        
        data_drift_report.run(reference_data=reference_data, current_data=current_data)
        
        output_path = self.output_dir / filename
        data_drift_report.save_html(str(output_path))
        logger.info(f"Reporte HTML de drift guardado en: {output_path}")
        
        # Extraer resultado en formato diccionario para la lógica de alertas
        report_dict = data_drift_report.as_dict()
        dataset_drift = report_dict["metrics"][0]["result"]["dataset_drift"]
        
        if dataset_drift:
            logger.warning("¡ALERTA! Se ha detectado Data Drift en el dataset actual frente a la referencia.")
        else:
            logger.info("No se ha detectado Data Drift significativo.")
            
        return dataset_drift
