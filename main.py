"""
SCOREIA — Entry Point Principal
================================
Punto de entrada unificado del sistema via CLI.

Uso:
    python main.py --mode train
    python main.py --mode predict --input data/raw/nuevas_solicitudes.csv
    python main.py --mode monitor --reference data/raw/credit_data_synthetic.csv
"""

import argparse
import sys
import logging
from pathlib import Path

# Asegurar que src/ está en el path
sys.path.insert(0, str(Path(__file__).parent / "src"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("SCOREIA")


def parse_args() -> argparse.Namespace:
    """Define y parsea los argumentos del CLI."""
    parser = argparse.ArgumentParser(
        prog="SCOREIA",
        description="Sistema de Credit Scoring Basado en Inteligencia Artificial",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python main.py --mode train
  python main.py --mode predict --input data/raw/nuevas_solicitudes.csv
  python main.py --mode monitor
        """,
    )

    parser.add_argument(
        "--mode",
        type=str,
        required=True,
        choices=["train", "predict", "monitor"],
        help="Modo de ejecución del sistema",
    )

    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Ruta al archivo de entrada para predicción (CSV)",
    )

    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Ruta al archivo de configuración (default: config.yaml)",
    )

    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Ruta de salida para resultados (CSV/JSON)",
    )

    return parser.parse_args()


def run_training(config_path: str) -> None:
    """Ejecuta el pipeline completo de entrenamiento."""
    logger.info("=" * 60)
    logger.info("  SCOREIA — Modo: ENTRENAMIENTO")
    logger.info("=" * 60)
    try:
        from module3_training.trainer import SCOREIATrainer
        trainer = SCOREIATrainer(config_path=config_path)
        result = trainer.run()
        logger.info("Pipeline de entrenamiento ejecutado exitosamente.")
    except Exception as e:
        logger.error(f"Error durante el entrenamiento: {e}", exc_info=True)
        sys.exit(1)


def run_prediction(config_path: str, input_path: str, output_path: str) -> None:
    """Ejecuta predicción e inferencia sobre nuevas solicitudes."""
    logger.info("=" * 60)
    logger.info("  SCOREIA — Modo: PREDICCIÓN")
    logger.info("=" * 60)
    # TODO: Implementar en Módulo 4
    # from module4_inference.predictor import SCOREIAPredictor
    # predictor = SCOREIAPredictor(config_path=config_path)
    # predictor.predict(input_path, output_path)
    logger.info("Pipeline de inferencia (Módulo 4) — Próximamente")


def run_monitoring(config_path: str) -> None:
    """Ejecuta detección de drift y auditoría de equidad."""
    logger.info("=" * 60)
    logger.info("  SCOREIA — Modo: MONITOREO")
    logger.info("=" * 60)
    # TODO: Implementar en Módulo 5
    # from module5_monitoring.drift_detector import DriftDetector
    # detector = DriftDetector(config_path=config_path)
    # detector.run()
    logger.info("Pipeline de monitoreo (Módulo 5) — Próximamente")


def main() -> None:
    """Función principal del sistema SCOREIA."""
    args = parse_args()

    logger.info("Iniciando SCOREIA v1.0.0")
    logger.info(f"Config: {args.config} | Modo: {args.mode}")

    if args.mode == "train":
        run_training(args.config)

    elif args.mode == "predict":
        if not args.input:
            logger.error("--input es requerido para el modo 'predict'")
            sys.exit(1)
        run_prediction(args.config, args.input, args.output)

    elif args.mode == "monitor":
        run_monitoring(args.config)

    logger.info("SCOREIA — Ejecución finalizada correctamente.")


if __name__ == "__main__":
    main()
