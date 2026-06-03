"""
SCOREIA — Generador de Dataset Sintético
==========================================
Genera un dataset de 10,000 registros con desbalanceo realista
(80% pagan / 20% incumplen) que replica las 16 variables del diseño
de SCOREIA con correlaciones estadísticamente coherentes.

Las relaciones entre variables y el label siguen lógica crediticia real:
  - Mayor score_buro  → menor probabilidad de incumplimiento
  - Mayor ratio_deuda_ingreso → mayor probabilidad de incumplimiento
  - Mayor meses_mora_maxima → mayor probabilidad de incumplimiento
  - Mayor ingreso_mensual → menor probabilidad de incumplimiento
  - Contrato Independiente → mayor riesgo que Indefinido
  etc.

Uso:
    python data/generate_synthetic_data.py
    python data/generate_synthetic_data.py --n_samples 5000 --output mi_dataset.csv
"""

import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from tqdm import tqdm

# ─── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("DataGenerator")

# ─── Semilla global ──────────────────────────────────────────────────────────
RANDOM_SEED = 42
rng = np.random.default_rng(RANDOM_SEED)


# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def _sigmoid(x: np.ndarray) -> np.ndarray:
    """Función sigmoide para convertir scores en probabilidades."""
    return 1.0 / (1.0 + np.exp(-x))


def _generate_base_features(n_samples: int) -> pd.DataFrame:
    """
    Genera las 16 variables predictoras base con distribuciones realistas.
    En este paso NO hay correlación forzada con el label (se añade después).
    """
    logger.info(f"Generando {n_samples:,} registros de variables base...")

    # ─── F01: edad (18–75 años) ───────────────────────────────────────────
    edad = rng.integers(low=18, high=76, size=n_samples)

    # ─── F02: estado_civil ────────────────────────────────────────────────
    # Proporciones aproximadas de la población adulta general
    estado_civil = rng.choice(
        ["Soltero", "Casado", "Divorciado", "Viudo"],
        size=n_samples,
        p=[0.35, 0.45, 0.15, 0.05],
    )

    # ─── F03: nivel_educativo (ordinal) ──────────────────────────────────
    nivel_educativo = rng.choice(
        ["Primaria", "Secundaria", "Universidad", "Posgrado"],
        size=n_samples,
        p=[0.10, 0.35, 0.42, 0.13],
    )

    # ─── F04: tipo_vivienda ───────────────────────────────────────────────
    tipo_vivienda = rng.choice(
        ["Propia", "Arrendada", "Familiar"],
        size=n_samples,
        p=[0.35, 0.40, 0.25],
    )

    # ─── F05: ingreso_mensual (USD, distribución log-normal) ─────────────
    # Log-normal con media ~$2,500 y asimetría positiva realista
    ingreso_mensual = np.exp(
        rng.normal(loc=7.8, scale=0.6, size=n_samples)  # e^7.8 ≈ 2440
    ).clip(min=500.0, max=20000.0).round(2)

    # ─── F06: antiguedad_laboral (meses, 0-360) ───────────────────────────
    # La mayoría entre 0 y 120 meses (0-10 años)
    antiguedad_laboral = rng.integers(low=0, high=361, size=n_samples)

    # ─── F07: tipo_contrato ───────────────────────────────────────────────
    tipo_contrato = rng.choice(
        ["Indefinido", "Temporal", "Independiente"],
        size=n_samples,
        p=[0.50, 0.30, 0.20],
    )

    # ─── F08: score_buro (300-850) ────────────────────────────────────────
    # Distribución normal centrada en ~620 (score medio-bajo)
    score_buro = rng.normal(loc=620, scale=90, size=n_samples).clip(300, 850).astype(int)

    # ─── F09: meses_mora_maxima (0-24) ───────────────────────────────────
    # Distribución muy sesgada a la derecha (la mayoría sin mora)
    meses_mora_maxima = rng.choice(
        range(25),
        size=n_samples,
        p=_generate_mora_probabilities(),
    )

    # ─── F10: num_creditos_activos (0-10) ─────────────────────────────────
    num_creditos_activos = rng.integers(low=0, high=11, size=n_samples)

    # ─── F11: consultas_buro_6m (0-15) ───────────────────────────────────
    # Poisson con lambda=2 (mayoría entre 0 y 5)
    consultas_buro_6m = rng.poisson(lam=2.0, size=n_samples).clip(0, 15).astype(int)

    # ─── F12: ratio_deuda_ingreso (0.0-1.5) ──────────────────────────────
    ratio_deuda_ingreso = rng.beta(a=2, b=4, size=n_samples).round(4) * 1.5

    # ─── F13: utilizacion_credito (0.0-1.0) ──────────────────────────────
    utilizacion_credito = rng.beta(a=2, b=3, size=n_samples).round(4)

    # ─── F14: monto_solicitado (USD, 500-50000) ───────────────────────────
    # Log-normal: la mayoría solicita entre $1,000 y $15,000
    monto_solicitado = np.exp(
        rng.normal(loc=8.5, scale=0.9, size=n_samples)
    ).clip(min=500.0, max=50000.0).round(2)

    # ─── F15: plazo_meses ─────────────────────────────────────────────────
    plazo_meses = rng.choice(
        [6, 12, 18, 24, 36, 48, 60, 72, 84],
        size=n_samples,
        p=[0.05, 0.15, 0.12, 0.20, 0.22, 0.12, 0.08, 0.04, 0.02],
    )

    # ─── F16: tipo_prestamo ───────────────────────────────────────────────
    tipo_prestamo = rng.choice(
        ["Personal", "Hipotecario", "Automotriz", "Tarjeta"],
        size=n_samples,
        p=[0.40, 0.25, 0.20, 0.15],
    )

    df = pd.DataFrame({
        "edad":               edad,
        "estado_civil":       estado_civil,
        "nivel_educativo":    nivel_educativo,
        "tipo_vivienda":      tipo_vivienda,
        "ingreso_mensual":    ingreso_mensual,
        "antiguedad_laboral": antiguedad_laboral,
        "tipo_contrato":      tipo_contrato,
        "score_buro":         score_buro,
        "meses_mora_maxima":  meses_mora_maxima,
        "num_creditos_activos": num_creditos_activos,
        "consultas_buro_6m":  consultas_buro_6m,
        "ratio_deuda_ingreso": ratio_deuda_ingreso,
        "utilizacion_credito": utilizacion_credito,
        "monto_solicitado":   monto_solicitado,
        "plazo_meses":        plazo_meses,
        "tipo_prestamo":      tipo_prestamo,
    })

    return df


def _generate_mora_probabilities() -> list:
    """
    Genera probabilidades para meses_mora_maxima (0-24).
    La distribución está muy sesgada: la mayoría de clientes tiene 0 meses de mora.
    """
    probs = np.array([0.60] + [0.02] * 24)  # 60% sin mora
    # Añadir un pequeño gradiente para valores bajos
    probs[1:6] = [0.08, 0.07, 0.06, 0.05, 0.04]
    probs[6:12] = 0.015
    probs[12:] = 0.005
    probs /= probs.sum()  # Normalizar para que sumen 1
    return probs.tolist()


def _compute_default_score(df: pd.DataFrame) -> np.ndarray:
    """
    Calcula un score de riesgo de incumplimiento para cada registro.
    Este score captura relaciones crediticias reales entre variables y el label.

    Lógica financiera aplicada:
    - score_buro NEGATIVO: mayor score = menor riesgo
    - ratio_deuda_ingreso POSITIVO: mayor ratio = mayor riesgo
    - meses_mora_maxima POSITIVO: historial negativo = mayor riesgo
    - ingreso_mensual NEGATIVO: más ingreso = menor riesgo
    - antigüedad laboral NEGATIVO: más estabilidad = menor riesgo
    - consultas_buro_6m POSITIVO: muchas consultas = señal de necesidad
    - utilizacion_credito POSITIVO: alta utilización = mayor riesgo
    """
    # Normalización de variables numéricas para el score
    score_norm = (df["score_buro"] - 300) / 550          # 0=malo, 1=excelente
    ingreso_norm = np.log1p(df["ingreso_mensual"]) / np.log1p(20000)  # 0-1
    antiguedad_norm = df["antiguedad_laboral"] / 360      # 0-1

    # ─── Intercepto base (sesgo hacia no incumplimiento) ─────────────────
    # -1.5 para que la probabilidad base sea ~18%
    logit = (
        -1.50                                              # Intercepto
        - 3.50 * score_norm                                # Buen score → bajo riesgo
        + 2.80 * df["ratio_deuda_ingreso"]                 # Más deuda → más riesgo
        + 0.18 * df["meses_mora_maxima"]                   # Historial negativo
        - 1.20 * ingreso_norm                              # Más ingreso → menos riesgo
        - 0.80 * antiguedad_norm                           # Más estabilidad → menos riesgo
        + 0.15 * df["consultas_buro_6m"]                   # Múltiples consultas
        + 1.50 * df["utilizacion_credito"]                 # Alta utilización
        + 0.40 * (df["tipo_contrato"] == "Independiente").astype(float)
        + 0.30 * (df["tipo_contrato"] == "Temporal").astype(float)
        - 0.50 * (df["tipo_vivienda"] == "Propia").astype(float)
        - 0.30 * (df["nivel_educativo"] == "Posgrado").astype(float)
        - 0.20 * (df["nivel_educativo"] == "Universidad").astype(float)
        + 0.20 * (df["nivel_educativo"] == "Primaria").astype(float)
    )

    return logit


def _assign_labels(df: pd.DataFrame, target_default_rate: float = 0.20) -> np.ndarray:
    """
    Asigna el label de incumplimiento usando el score logístico con ajuste
    de threshold para alcanzar exactamente el desbalanceo objetivo.

    Args:
        df: DataFrame con las features generadas.
        target_default_rate: Proporción objetivo de incumplimientos (0.20 = 20%).

    Returns:
        Array numpy con labels binarios (0=Pagó, 1=Incumplió).
    """
    logger.info(f"Calculando scores de riesgo crediticio...")
    logit = _compute_default_score(df)

    # Añadir ruido gaussiano para simular factores no observados
    noise = rng.normal(loc=0.0, scale=0.5, size=len(df))
    logit_noisy = logit + noise

    # Convertir a probabilidades
    pd_scores = _sigmoid(logit_noisy)

    # Ajustar threshold para alcanzar exactamente el target_default_rate
    # Buscamos el threshold t tal que P(pd_scores > t) ≈ target_default_rate
    threshold = np.percentile(pd_scores, (1 - target_default_rate) * 100)
    labels = (pd_scores >= threshold).astype(int)

    actual_rate = labels.mean()
    logger.info(
        f"Tasa de incumplimiento generada: {actual_rate:.2%} "
        f"(objetivo: {target_default_rate:.2%})"
    )

    return labels


def _inject_missing_values(df: pd.DataFrame, missing_rate: float = 0.02) -> pd.DataFrame:
    """
    Inyecta un pequeño porcentaje de valores nulos para simular datos reales.
    Solo en columnas donde la ausencia de datos tiene sentido crediticio.

    Args:
        df: DataFrame completo.
        missing_rate: Porcentaje de nulos por columna (default 2%).
    """
    logger.info(f"Inyectando ~{missing_rate:.0%} de valores nulos para realismo...")

    # Columnas que pueden tener nulos razonables
    nullable_columns = [
        "score_buro",           # Clientes sin historial crediticio
        "meses_mora_maxima",    # Sin historial
        "consultas_buro_6m",    # Sin historial
        "utilizacion_credito",  # Sin créditos activos
        "antiguedad_laboral",   # Desempleados
    ]

    df_copy = df.copy()
    n_rows = len(df_copy)

    for col in nullable_columns:
        n_missing = int(n_rows * missing_rate)
        missing_idx = rng.choice(n_rows, size=n_missing, replace=False)
        df_copy.loc[missing_idx, col] = np.nan

    total_missing = df_copy.isnull().sum().sum()
    logger.info(f"Total de valores nulos inyectados: {total_missing:,}")

    return df_copy


def _validate_dataset(df: pd.DataFrame) -> None:
    """
    Valida que el dataset generado cumple con las especificaciones de SCOREIA.
    Lanza AssertionError si alguna validación falla.
    """
    logger.info("Validando integridad del dataset...")

    # Verificar columnas exactas
    expected_cols = [
        "edad", "estado_civil", "nivel_educativo", "tipo_vivienda",
        "ingreso_mensual", "antiguedad_laboral", "tipo_contrato",
        "score_buro", "meses_mora_maxima", "num_creditos_activos",
        "consultas_buro_6m", "ratio_deuda_ingreso", "utilizacion_credito",
        "monto_solicitado", "plazo_meses", "tipo_prestamo", "incumplimiento",
    ]
    assert list(df.columns) == expected_cols, \
        f"Columnas no coinciden con el diseño. Esperadas: {expected_cols}"

    # Verificar rangos numéricos
    assert df["edad"].between(18, 75).all(), "edad fuera de rango [18, 75]"
    assert df["score_buro"].dropna().between(300, 850).all(), \
        "score_buro fuera de rango [300, 850]"
    assert df["incumplimiento"].isin([0, 1]).all(), "label debe ser 0 o 1"
    assert df["plazo_meses"].isin([6, 12, 18, 24, 36, 48, 60, 72, 84]).all(), \
        "plazo_meses con valores inesperados"

    # Verificar categorías
    assert set(df["estado_civil"].unique()).issubset(
        {"Soltero", "Casado", "Divorciado", "Viudo"}
    )
    assert set(df["nivel_educativo"].unique()).issubset(
        {"Primaria", "Secundaria", "Universidad", "Posgrado"}
    )

    # Verificar desbalanceo (±5% del objetivo)
    default_rate = df["incumplimiento"].mean()
    assert 0.15 <= default_rate <= 0.25, \
        f"Tasa de incumplimiento {default_rate:.2%} fuera del rango esperado [15%, 25%]"

    logger.info("✅ Todas las validaciones pasaron correctamente.")


def _print_summary(df: pd.DataFrame, output_path: Path) -> None:
    """Imprime un resumen estadístico del dataset generado."""
    default_rate = df["incumplimiento"].mean()
    n_default = df["incumplimiento"].sum()
    n_paid = len(df) - n_default

    print("\n" + "=" * 60)
    print("  SCOREIA -- RESUMEN DEL DATASET SINTETICO GENERADO")
    print("=" * 60)
    print(f"  [*] Total de registros    : {len(df):>10,}")
    print(f"  [OK] Pagaron (label=0)    : {n_paid:>10,}  ({1-default_rate:.1%})")
    print(f"  [!!] Incumplieron (lbl=1) : {n_default:>10,}  ({default_rate:.1%})")
    print(f"  [>] Archivo guardado en   : {output_path}")
    print(f"  [#] Total de columnas     : {len(df.columns)} (16 features + 1 label)")
    print(f"  [?] Valores nulos totales : {df.isnull().sum().sum():>10,}")
    print("=" * 60)

    print("\n-- Estadisticas Numericas Clave ---------------------------")
    numeric_cols = [
        "edad", "ingreso_mensual", "score_buro", "ratio_deuda_ingreso",
        "meses_mora_maxima", "monto_solicitado"
    ]
    print(df[numeric_cols].describe().round(2).to_string())

    print("\n-- Distribucion del Label por Variable Clave --------------")
    print(f"\n  Por tipo_contrato:\n{df.groupby('tipo_contrato')['incumplimiento'].mean().round(3)}")
    print(f"\n  Por nivel_educativo:\n{df.groupby('nivel_educativo')['incumplimiento'].mean().round(3)}")
    print(f"\n  Por tipo_vivienda:\n{df.groupby('tipo_vivienda')['incumplimiento'].mean().round(3)}")
    print()


# =============================================================================
# FUNCIÓN PRINCIPAL
# =============================================================================

def generate_dataset(
    n_samples: int = 10_000,
    target_default_rate: float = 0.20,
    missing_rate: float = 0.02,
    output_dir: str = "data/raw",
    output_filename: str = "credit_data_synthetic.csv",
    random_seed: int = 42,
) -> pd.DataFrame:
    """
    Genera el dataset sintético completo de SCOREIA.

    Args:
        n_samples: Número de registros a generar (default 10,000).
        target_default_rate: Proporción de incumplimientos (default 0.20 = 20%).
        missing_rate: Porcentaje de valores nulos por columna (default 0.02 = 2%).
        output_dir: Directorio de salida.
        output_filename: Nombre del archivo CSV de salida.
        random_seed: Semilla para reproducibilidad.

    Returns:
        DataFrame con el dataset completo.
    """
    global rng
    rng = np.random.default_rng(random_seed)

    logger.info("=" * 60)
    logger.info("  SCOREIA — Generador de Dataset Sintético")
    logger.info("=" * 60)
    logger.info(f"  n_samples       = {n_samples:,}")
    logger.info(f"  default_rate    = {target_default_rate:.0%}")
    logger.info(f"  missing_rate    = {missing_rate:.0%}")
    logger.info(f"  random_seed     = {random_seed}")
    logger.info("=" * 60)

    # PASO 1: Generar variables base
    df = _generate_base_features(n_samples)

    # PASO 2: Asignar labels con correlaciones crediticias realistas
    labels = _assign_labels(df, target_default_rate=target_default_rate)
    df["incumplimiento"] = labels

    # PASO 3: Inyectar valores nulos para realismo
    df = _inject_missing_values(df, missing_rate=missing_rate)

    # PASO 4: Reordenar columnas en el orden exacto del diseño de SCOREIA
    column_order = [
        "edad", "estado_civil", "nivel_educativo", "tipo_vivienda",
        "ingreso_mensual", "antiguedad_laboral", "tipo_contrato",
        "score_buro", "meses_mora_maxima", "num_creditos_activos",
        "consultas_buro_6m", "ratio_deuda_ingreso", "utilizacion_credito",
        "monto_solicitado", "plazo_meses", "tipo_prestamo", "incumplimiento",
    ]
    df = df[column_order]

    # PASO 5: Validar integridad del dataset
    _validate_dataset(df)

    # PASO 6: Guardar en disco
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    full_path = output_path / output_filename
    df.to_csv(full_path, index=False, encoding="utf-8")
    logger.info(f"Dataset guardado exitosamente en: {full_path}")

    # PASO 7: Imprimir resumen
    _print_summary(df, full_path)

    return df


# =============================================================================
# CLI
# =============================================================================

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generador de Dataset Sintético — SCOREIA Credit Scoring",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--n_samples", type=int, default=10_000,
        help="Número de registros a generar"
    )
    parser.add_argument(
        "--default_rate", type=float, default=0.20,
        help="Proporción de incumplimientos (0.20 = 20%%)"
    )
    parser.add_argument(
        "--missing_rate", type=float, default=0.02,
        help="Porcentaje de valores nulos por columna"
    )
    parser.add_argument(
        "--output_dir", type=str, default="data/raw",
        help="Directorio de salida"
    )
    parser.add_argument(
        "--output_filename", type=str, default="credit_data_synthetic.csv",
        help="Nombre del archivo CSV de salida"
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Semilla aleatoria para reproducibilidad"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    generate_dataset(
        n_samples=args.n_samples,
        target_default_rate=args.default_rate,
        missing_rate=args.missing_rate,
        output_dir=args.output_dir,
        output_filename=args.output_filename,
        random_seed=args.seed,
    )
