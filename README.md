# SCOREIA

Inteligencia de Riesgo Crediticio y Decisiones Automatizadas.

## Descripcion General

SCOREIA es un motor de evaluacion de riesgo crediticio de ultima generacion disenado para instituciones financieras. Utiliza un modelo de clasificacion (Random Forest) entrenado con datos historicos para evaluar el perfil de riesgo de los solicitantes de credito en menos de 200 milisegundos. 

La plataforma no funciona como una caja negra; integra un modulo de interpretabilidad (XAI) basado en valores SHAP, permitiendo a los analistas comprender exactamente que factores influyeron en la aprobacion o rechazo de cada solicitud.

## Caracteristicas Principales

- Evaluacion instantanea de riesgo con modelos de Machine Learning predictivos.
- Simulador "What-If" para ajustar montos y plazos en tiempo real.
- Panel de administracion y vista unificada de analisis.
- Sistema de explicabilidad (XAI) para cumplimiento normativo.
- Autenticacion segura mediante cifrado bcrypt nativo.
- UI/UX premium con tipografia moderna y diseño de paneles de cristal oscuro.

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
4. Instalar las dependencias necesarias (especificadas en el entorno o usando pip install fastapi uvicorn sqlalchemy bcrypt pydantic scikit-learn pandas shap jinja2).
5. Configurar las credenciales SMTP en un archivo .env si se requiere la funcionalidad de envio de correos reales.

## Ejecucion del Servidor

Para iniciar la aplicacion, ejecutar el siguiente comando desde la raiz del proyecto:

python -m app.main_api

El servidor estara disponible en el puerto 8000 por defecto.
La aplicacion estara accesible en: http://localhost:8000

## Creditos

Desarrollado y diseñado por Andres Eloy Lopez.
Todos los derechos reservados, 2026.
