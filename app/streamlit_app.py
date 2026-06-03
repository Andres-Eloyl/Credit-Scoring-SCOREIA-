"""
SCOREIA — App Demo con Streamlit
==================================
Interfaz interactiva para demostración del sistema.
Se implementará en la Fase 6 del proyecto.

Uso:
    streamlit run app/streamlit_app.py
"""

import streamlit as st

st.set_page_config(
    page_title="SCOREIA — Credit Scoring AI",
    page_icon="🏦",
    layout="wide",
)

st.title("🏦 SCOREIA")
st.subheader("Sistema de Credit Scoring Basado en Inteligencia Artificial")

st.info(
    "⚙️ Esta interfaz estará disponible al completar el **Módulo 4** (Inferencia + XAI). "
    "Por ahora, el sistema está en fase de desarrollo activo."
)

st.markdown("""
### Estado del Proyecto
| Módulo | Estado |
|--------|--------|
| Módulo 1 — Preprocesamiento | 🔄 En desarrollo |
| Módulo 2 — Ingeniería de Variables | ⏳ Pendiente |
| Módulo 3 — Entrenamiento | ⏳ Pendiente |
| Módulo 4 — Inferencia + XAI | ⏳ Pendiente |
| Módulo 5 — Monitoreo | ⏳ Pendiente |
""")
