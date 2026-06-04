"""
SCOREIA — Módulo 3: Evaluador de Modelos
===========================================
Responsable de calcular métricas de evaluación del modelo entrenado,
generar gráficos de curvas de rendimiento y presentar reportes formales.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)

logger = logging.getLogger("SCOREIA.Evaluator")


class SCOREIAEvaluator:
    """
    Evalúa el rendimiento de los modelos entrenados y genera reportes
    y gráficos de métricas clave (Curva ROC, Curva PR, Matriz de Confusión).
    """

    def __init__(self, config: dict):
        """
        Args:
            config: Configuración central del sistema (diccionario).
        """
        self.config = config
        self.target_auc = config.get("metrics", {}).get("target_auc_roc", 0.80)
        self.target_f1 = config.get("metrics", {}).get("target_f1_score", 0.72)
        self.metrics_: Dict[str, float] = {}

    def evaluate(self, model: Any, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, float]:
        """
        Calcula las métricas de rendimiento sobre el conjunto de test.

        Args:
            model: Modelo entrenado.
            X_test: DataFrame de test con features seleccionadas.
            y_test: Serie de test con target real.

        Returns:
            Diccionario con métricas: auc_roc, f1_score, precision, recall, accuracy.
        """
        logger.info("Evaluando modelo en el conjunto de test...")

        # Predicciones
        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)[:, 1]

        # Calcular métricas básicas
        auc_roc = roc_auc_score(y_test, y_proba)
        f1 = f1_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)
        accuracy = accuracy_score(y_test, y_pred)

        # Encontrar umbral óptimo que maximiza F1-Score
        precisions, recalls, thresholds = precision_recall_curve(y_test, y_proba)
        f1_scores = 2 * (precisions * recalls) / (precisions + recalls + 1e-10)
        best_idx = np.argmax(f1_scores)
        opt_f1 = f1_scores[best_idx]
        opt_thresh = thresholds[best_idx] if best_idx < len(thresholds) else 0.50

        # Matriz de confusión
        cm = confusion_matrix(y_test, y_pred)
        tn, fp, fn, tp = cm.ravel()

        self.metrics_ = {
            "auc_roc": float(auc_roc),
            "f1_score": float(f1),
            "precision": float(precision),
            "recall": float(recall),
            "accuracy": float(accuracy),
            "opt_f1_score": float(opt_f1),
            "opt_threshold": float(opt_thresh),
            "true_negatives": int(tn),
            "false_positives": int(fp),
            "false_negatives": int(fn),
            "true_positives": int(tp),
        }

        logger.info(
            f"Métricas obtenidas: AUC-ROC={auc_roc:.4f} | F1-Score={f1:.4f} | "
            f"F1-Score Óptimo={opt_f1:.4f} (Umbral={opt_thresh:.3f})"
        )
        return self.metrics_

    def plot_curves(
        self,
        model: Any,
        X_test: pd.DataFrame,
        y_test: pd.Series,
        output_dir: str = "reports/figures",
    ) -> None:
        """
        Genera y guarda gráficos de evaluación: ROC, Precision-Recall y Matriz de Confusión.

        Args:
            model: Modelo entrenado.
            X_test: DataFrame de test con features.
            y_test: Serie de test con target.
            output_dir: Directorio para guardar las imágenes.
        """
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        y_proba = model.predict_proba(X_test)[:, 1]
        y_pred = model.predict(X_test)

        # ── Curva ROC ──────────────────────────────────────────────────
        fpr, tpr, _ = roc_curve(y_test, y_proba)
        auc_val = self.metrics_.get("auc_roc", roc_auc_score(y_test, y_proba))

        plt.figure(figsize=(8, 6))
        plt.plot(fpr, tpr, color="darkorange", lw=2, label=f"ROC curve (AUC = {auc_val:.3f})")
        plt.plot([0, 1], [0, 1], color="navy", lw=1.5, linestyle="--")
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel("Tasa de Falsos Positivos (FPR)")
        plt.ylabel("Tasa de Verdaderos Positivos (TPR)")
        plt.title("Curva ROC - Modelo SCOREIA")
        plt.legend(loc="lower right")
        plt.grid(True, linestyle=":", alpha=0.6)
        
        roc_path = out_path / "roc_curve.png"
        plt.savefig(roc_path, dpi=150, bbox_inches="tight")
        plt.close()
        logger.info(f"Curva ROC guardada en: {roc_path}")

        # ── Curva Precision-Recall ─────────────────────────────────────
        precision_vals, recall_vals, _ = precision_recall_curve(y_test, y_proba)
        f1_val = self.metrics_.get("f1_score", f1_score(y_test, y_pred))

        plt.figure(figsize=(8, 6))
        plt.plot(recall_vals, precision_vals, color="blue", lw=2, label=f"PR curve (F1 = {f1_val:.3f})")
        plt.xlabel("Recall (Sensibilidad)")
        plt.ylabel("Precision (Valor Predictivo Positivo)")
        plt.title("Curva Precision-Recall - Modelo SCOREIA")
        plt.legend(loc="lower left")
        plt.grid(True, linestyle=":", alpha=0.6)

        pr_path = out_path / "precision_recall_curve.png"
        plt.savefig(pr_path, dpi=150, bbox_inches="tight")
        plt.close()
        logger.info(f"Curva Precision-Recall guardada en: {pr_path}")

        # ── Matriz de Confusión ─────────────────────────────────────────
        cm = confusion_matrix(y_test, y_pred)
        
        plt.figure(figsize=(6, 5))
        sns.heatmap(
            cm,
            annot=True,
            fmt="d",
            cmap="Blues",
            xticklabels=["Pagó (0)", "Incumplió (1)"],
            yticklabels=["Pagó (0)", "Incumplió (1)"],
            cbar=False,
            annot_kws={"size": 14, "weight": "bold"}
        )
        plt.ylabel("Verdadero")
        plt.xlabel("Predicho")
        plt.title("Matriz de Confusión - SCOREIA")
        
        cm_path = out_path / "confusion_matrix.png"
        plt.savefig(cm_path, dpi=150, bbox_inches="tight")
        plt.close()
        logger.info(f"Matriz de Confusión guardada en: {cm_path}")

    def print_report(self) -> None:
        """
        Imprime un reporte detallado del desempeño del modelo en la consola.
        """
        if not self.metrics_:
            logger.error("Debe ejecutar evaluate() primero para generar el reporte.")
            return

        m = self.metrics_
        auc = m["auc_roc"]
        f1 = m["f1_score"]

        auc_ok = "[CUMPLIDO]" if auc >= self.target_auc else "[NO CUMPLIDO]"
        
        opt_f1 = m.get("opt_f1_score", f1)
        opt_thresh = m.get("opt_threshold", 0.50)
        
        # Se considera cumplido si al menos el F1 óptimo calibrado alcanza el target
        f1_ok = "[CUMPLIDO]" if f1 >= self.target_f1 else "[NO CUMPLIDO]"
        opt_f1_ok = "[CUMPLIDO]" if opt_f1 >= self.target_f1 else "[NO CUMPLIDO]"

        print("\n" + "=" * 65)
        print("  SCOREIA -- REPORTE FINAL DE EVALUACION DEL MODELO")
        print("=" * 65)
        print(f"  Metricas del Modelo frente a Objetivos:")
        print(f"  - AUC-ROC           : {auc:.4f}  (Meta: {self.target_auc:.2f}) -> {auc_ok}")
        print(f"  - F1-Score (Std 0.5): {f1:.4f}  (Meta: {self.target_f1:.2f}) -> {f1_ok}")
        print(f"  - F1-Score (Opt {opt_thresh:.2f}): {opt_f1:.4f}  (Meta: {self.target_f1:.2f}) -> {opt_f1_ok}")
        print("-" * 65)
        print(f"  Detalle de Metricas Secundarias:")
        print(f"  - Precision: {m['precision']:.4f}")
        print(f"  - Recall   : {m['recall']:.4f}")
        print(f"  - Accuracy : {m['accuracy']:.4f}")
        print("-" * 65)
        print(f"  Matriz de Confusion (Detalle Numerico):")
        print(f"    - Verdaderos Negativos (Pagó):        {m['true_negatives']}")
        print(f"    - Falsos Positivos (Predijo Incumplió): {m['false_positives']}")
        print(f"    - Falsos Negativos (Predijo Pagó):     {m['false_negatives']}")
        print(f"    - Verdaderos Positivos (Incumplió):     {m['true_positives']}")
        print("=" * 65 + "\n")
