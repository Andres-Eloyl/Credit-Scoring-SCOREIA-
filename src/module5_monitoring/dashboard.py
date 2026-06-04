import logging
import pandas as pd
from pathlib import Path
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset, DataQualityPreset, ClassificationPreset
from evidently import ColumnMapping

logger = logging.getLogger("SCOREIA.MonitoringDashboard")

class MonitoringDashboard:
    """
    Clase para generar un Dashboard Interactivo de Monitoreo en formato HTML
    utilizando la librería Evidently. Cubre Data Quality, Data Drift y Performance.
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        self.output_dir = Path("reports/monitoring")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_dashboard(self, ref_df: pd.DataFrame, curr_df: pd.DataFrame, 
                           target_col: str, pred_col: str, 
                           filename: str = "monitoring_dashboard.html") -> Path:
        """
        Ejecuta los cálculos y guarda el dashboard interactivo en un archivo HTML.
        
        Args:
            ref_df (pd.DataFrame): Datos de referencia (ej. entrenamiento).
            curr_df (pd.DataFrame): Datos actuales (ej. nuevos datos de producción).
            target_col (str): Nombre de la columna del ground truth.
            pred_col (str): Nombre de la columna de predicciones (clase predicha).
            filename (str): Nombre del archivo a generar.
            
        Returns:
            Path: Ruta al archivo HTML generado.
        """
        logger.info("Generando Dashboard de Monitoreo Interactivo con Evidently...")
        
        dashboard = Report(metrics=[
            DataQualityPreset(),
            DataDriftPreset(),
            ClassificationPreset(),
        ])
        
        column_mapping = ColumnMapping()
        column_mapping.target = target_col
        column_mapping.prediction = pred_col
        column_mapping.task = 'classification'
        # El resto de variables numéricas y categóricas serán inferidas automáticamente por Evidently
        
        try:
            dashboard.run(reference_data=ref_df, current_data=curr_df, column_mapping=column_mapping)
            
            output_path = self.output_dir / filename
            dashboard.save_html(str(output_path))
            logger.info(f"Dashboard interactivo guardado exitosamente en: {output_path}")
            
            return output_path
        except Exception as e:
            logger.error(f"Error generando el dashboard de evidently: {e}")
            raise e
