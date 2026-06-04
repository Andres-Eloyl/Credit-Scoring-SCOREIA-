import logging
import pandas as pd
import numpy as np
from typing import Dict, Any

logger = logging.getLogger("SCOREIA.FairnessAudit")

class FairnessAudit:
    """
    Clase para auditar la equidad del modelo de Credit Scoring, analizando si hay
    sesgos hacia grupos demográficos específicos (por ejemplo: estado civil o nivel educativo).
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        import yaml
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
            
        self.sensitive_features = self.config.get("monitoring", {}).get("fairness_sensitive_features", [])
        
    def _calculate_metrics(self, df_group: pd.DataFrame, target_col: str, pred_col: str) -> Dict[str, float]:
        """Calcula las métricas base para un grupo dado."""
        # En SCOREIA, target=1 significa Incumplimiento.
        # "Aprobación" (resultado favorable) significa predicción=0 (Pago).
        
        total = len(df_group)
        if total == 0:
            return {"approval_rate": 0.0, "tpr_approval": 0.0}
            
        # Tasa de aprobación: Porcentaje de préstamos concedidos (predicción = 0)
        approved = len(df_group[df_group[pred_col] == 0])
        approval_rate = approved / total
        
        # True Positive Rate de Aprobación (Proporción de los que realmente iban a pagar que fueron aprobados)
        # Esto es equivalente a la Especificidad (TNR) si consideramos la clase 1 como el objetivo del modelo.
        real_payers = df_group[df_group[target_col] == 0]
        if len(real_payers) > 0:
            correctly_approved = len(real_payers[real_payers[pred_col] == 0])
            tpr_approval = correctly_approved / len(real_payers)
        else:
            tpr_approval = 0.0
            
        return {
            "approval_rate": approval_rate,
            "tpr_approval": tpr_approval,
            "count": total
        }

    def audit(self, df: pd.DataFrame, target_col: str, pred_col: str) -> Dict[str, Any]:
        """
        Ejecuta la auditoría sobre un DataFrame de validación o monitoreo.
        
        Args:
            df (pd.DataFrame): DataFrame con features, targets reales y predicciones.
            target_col (str): Nombre de la columna con el ground truth (0 = Pagó, 1 = Incumplió).
            pred_col (str): Nombre de la columna con la predicción del modelo (0 o 1).
            
        Returns:
            Dict con los resultados del análisis de equidad.
        """
        results = {}
        logger.info("Iniciando auditoría de equidad (Fairness Audit)...")
        
        for feature in self.sensitive_features:
            if feature not in df.columns:
                logger.warning(f"La variable sensible '{feature}' no se encuentra en el dataset.")
                continue
                
            groups = df[feature].unique()
            feature_metrics = {}
            
            for group in groups:
                df_group = df[df[feature] == group]
                feature_metrics[str(group)] = self._calculate_metrics(df_group, target_col, pred_col)
                
            # Calcular Disparate Impact (DI) y Equal Opportunity Difference (EOD)
            # Usaremos el grupo mayoritario como referencia por defecto
            majority_group = str(df[feature].mode()[0])
            ref_approval_rate = feature_metrics[majority_group]["approval_rate"]
            ref_tpr_approval = feature_metrics[majority_group]["tpr_approval"]
            
            disparities = {}
            for group, metrics in feature_metrics.items():
                if group == majority_group:
                    continue
                    
                # Disparate Impact: Ratio de tasas de aprobación (Idealmente entre 0.8 y 1.25)
                # Si DI < 0.8, el grupo tiene un impacto adverso.
                if ref_approval_rate > 0:
                    di = metrics["approval_rate"] / ref_approval_rate
                else:
                    di = 1.0
                    
                # Equal Opportunity Difference: Diferencia en TPR de aprobación (Idealmente cerca de 0.0)
                eod = metrics["tpr_approval"] - ref_tpr_approval
                
                disparities[group] = {
                    "disparate_impact": round(di, 4),
                    "equal_opportunity_diff": round(eod, 4)
                }
                
                if di < 0.8:
                    logger.warning(f"Posible sesgo adverso en '{feature}={group}'. Disparate Impact: {di:.2f} (< 0.8)")
                
            results[feature] = {
                "reference_group": majority_group,
                "group_metrics": feature_metrics,
                "disparities": disparities
            }
            
        logger.info("Auditoría de equidad completada.")
        return results
