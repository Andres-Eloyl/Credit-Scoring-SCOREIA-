# SCOREIA

Inteligencia de Riesgo Crediticio y Decisiones Automatizadas.

## Descripcion General

SCOREIA es un motor de evaluacion de riesgo crediticio de ultima generacion disenado para instituciones financieras. Utiliza un modelo de clasificacion (Random Forest) entrenado con datos historicos para evaluar el perfil de riesgo de los solicitantes de credito en menos de 200 milisegundos. 

La plataforma no funciona como una caja negra; integra un modulo de interpretabilidad (XAI) basado en valores SHAP, permitiendo a los analistas comprender exactamente que factores influyeron en la aprobacion o rechazo de cada solicitud.

## Caracteristicas Principales

- Evaluación instantánea de riesgo con modelos de Machine Learning predictivos.
- Simulador "What-If" para ajustar montos y plazos en tiempo real.
- Sistema de explicabilidad (XAI) basado en gráficos Waterfall de valores SHAP.
- Módulo de Auditoría y Trazabilidad (Historial detallado por analista).
- Generación y exportación de reportes dinámicos a PDF.
- Panel de Soporte con monitoreo de estado y diagnóstico en vivo del servidor.
- Autenticación segura mediante cifrado bcrypt nativo.
- UI/UX premium con tipografía moderna y diseño de paneles de cristal oscuro.

## Arquitectura

- Backend: FastAPI (Python)
- Base de Datos: SQLite (SQLAlchemy ORM)
- Seguridad: Hashing Bcrypt
- Interfaz de Usuario: HTML5, CSS Vanilla, JavaScript, TailwindCSS (via CDN)
- Graficos: ApexCharts
- Exportacion de Reportes: html2pdf.js

## Requisitos de Instalacion

- Python 3.10 o superior
- Entorno virtual recomendado (venv)

## Instrucciones de Instalacion

1. Clonar el repositorio.
2. Crear un entorno virtual:
   python -m venv venv
3. Activar el entorno virtual:
   - Windows: venv\Scripts\activate
   - Unix/MacOS: source venv/bin/activate
4. Instalar las dependencias necesarias:
   pip install -r requirements.txt
5. Configurar las credenciales en un archivo `.env` (opcional).

## Ejecucion del Servidor

Para iniciar la aplicacion, ejecuta el servidor ASGI desde la raíz del proyecto:

uvicorn app.main_api:app --host 127.0.0.1 --port 8000 --reload

El servidor estara disponible en el puerto 8000.
La aplicacion y la interfaz estarán accesibles en: http://localhost:8000

## Creditos

Desarrollado y diseñado por Andres Eloy Lopez.
Todos los derechos reservados, 2026.
