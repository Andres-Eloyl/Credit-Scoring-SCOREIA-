import yaml

class RiskSegmentor:
    """
    Segmenta el riesgo basado en la Probabilidad de Incumplimiento (PD).
    Las reglas se configuran a través del archivo config.yaml.
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Inicializa el segmentador de riesgo leyendo los umbrales del config.yaml.
        
        Args:
            config_path (str): Ruta al archivo YAML de configuración.
        """
        with open(config_path, "r", encoding="utf-8") as file:
            self.config = yaml.safe_load(file)
            
        self.inference_config = self.config.get("inference", {})
        self.thresholds = self.inference_config.get("risk_thresholds", {})
        self.labels = self.inference_config.get("risk_labels", {})
        
        # Extraer umbrales superiores de bajo y medio
        self.low_upper = self.thresholds.get("low", [0.0, 0.30])[1]
        self.medium_upper = self.thresholds.get("medium", [0.30, 0.60])[1]
        
    def segment(self, pd: float) -> str:
        """
        Devuelve el segmento de riesgo para una PD dada.
        
        Args:
            pd (float): Probabilidad de incumplimiento (0.0 a 1.0).
            
        Returns:
            str: "Bajo", "Medio" o "Alto".
        """
        if pd < self.low_upper:
            return self.labels.get("low", "Bajo")
        elif pd < self.medium_upper:
            return self.labels.get("medium", "Medio")
        else:
            return self.labels.get("high", "Alto")
