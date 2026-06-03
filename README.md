# SCOREIA 🏦
## Sistema de Credit Scoring Basado en Inteligencia Artificial

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![ML](https://img.shields.io/badge/Algorithm-Random%20Forest-orange.svg)]()
[![XAI](https://img.shields.io/badge/XAI-SHAP-purple.svg)]()

---

### 📌 Descripción

SCOREIA es un sistema end-to-end de **Credit Scoring** que predice la **Probabilidad de Incumplimiento (PD)** de solicitantes de crédito bancario mediante clasificación binaria supervisada. El sistema combina:

- **Random Forest Classifier** optimizado con búsqueda bayesiana de hiperparámetros
- **SMOTE** para manejo del desbalanceo de clases (80% pago / 20% incumplimiento)
- **SHAP Values** para explicabilidad individual de cada decisión crediticia
- **Evidently** para monitoreo de concept drift y auditoría de equidad

---

### 🎯 Métricas Objetivo

| Métrica | Objetivo |
|---|---|
| AUC-ROC | ≥ 0.80 |
| F1-Score | ≥ 0.72 |

---

### 🗂️ Estructura del Proyecto

```
SCOREIA/
├── data/
│   ├── raw/                    # Datos originales (no versionados)
│   ├── processed/              # Datos transformados
│   └── external/               # Datos externos de referencia
├── notebooks/                  # Análisis exploratorio y experimentos
├── src/
│   ├── module1_preprocessing/  # Limpieza, imputación, OHE, SMOTE
│   ├── module2_features/       # Ratios financieros, WoE, selección
│   ├── module3_training/       # Entrenamiento, CV, serialización
│   ├── module4_inference/      # Predicción, segmentación, SHAP
│   └── module5_monitoring/     # Drift detection, fairness audit
├── models/                     # Modelos serializados (.pkl)
├── reports/                    # Gráficos, reportes HTML y JSON
├── tests/                      # Tests unitarios con pytest
├── app/                        # Demo interactiva con Streamlit
├── config.yaml                 # Configuración central
├── requirements.txt            # Dependencias Python 3.11
└── main.py                     # Entry point CLI
```

---

### ⚙️ Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/Andres-Eloyl/Credit-Scoring-SCOREIA-.git
cd Credit-Scoring-SCOREIA-

# 2. Crear entorno virtual (Python 3.11)
python -m venv venv
venv\Scripts\activate   # Windows

# 3. Instalar dependencias
pip install -r requirements.txt
```

---

### 🚀 Uso Rápido

```bash
# Generar dataset sintético
python data/generate_synthetic_data.py

# Entrenar el modelo completo
python main.py --mode train

# Inferencia sobre nuevas solicitudes
python main.py --mode predict --input data/raw/nuevas_solicitudes.csv

# Lanzar demo interactiva
streamlit run app/streamlit_app.py
```

---

### 🏗️ Arquitectura de los Módulos

| Módulo | Responsabilidad |
|---|---|
| **Módulo 1** | Ingesta, limpieza, imputación, OHE, SMOTE |
| **Módulo 2** | Ratios financieros, Weight of Evidence, selección de variables |
| **Módulo 3** | Entrenamiento RF, K-Fold CV, MLflow tracking, serialización |
| **Módulo 4** | Predicción, segmentación de riesgo (Bajo/Medio/Alto), SHAP |
| **Módulo 5** | Detección de concept drift, auditoría de equidad |

---

### 📊 Variables del Modelo

| Código | Variable | Tipo |
|---|---|---|
| F01 | edad | Numérico entero |
| F02 | estado_civil | Categórico (Soltero/Casado/Divorciado/Viudo) |
| F03 | nivel_educativo | Ordinal (Primaria→Secundaria→Universidad→Posgrado) |
| F04 | tipo_vivienda | Categórico (Propia/Arrendada/Familiar) |
| F05 | ingreso_mensual | Numérico float (USD) |
| F06 | antiguedad_laboral | Numérico entero (meses) |
| F07 | tipo_contrato | Categórico (Indefinido/Temporal/Independiente) |
| F08 | score_buro | Numérico entero (300-850) |
| F09 | meses_mora_maxima | Numérico entero |
| F10 | num_creditos_activos | Numérico entero |
| F11 | consultas_buro_6m | Numérico entero |
| F12 | ratio_deuda_ingreso | Numérico float |
| F13 | utilizacion_credito | Numérico float |
| F14 | monto_solicitado | Numérico float (USD) |
| F15 | plazo_meses | Numérico entero |
| F16 | tipo_prestamo | Categórico (Personal/Hipotecario/Automotriz/Tarjeta) |
| **LABEL** | **incumplimiento** | **Binario (0=Pagó, 1=Incumplió)** |

---

### 📄 Licencia

MIT License — Ver [LICENSE](LICENSE) para detalles.
