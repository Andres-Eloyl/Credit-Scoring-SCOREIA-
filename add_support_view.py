import os
import re

html_path = r'app\ui\app.html'
with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

# Add nav-support button below nav-config
nav_config = """        <a id="nav-config" class="text-cream/50 hover:bg-cream/5 hover:text-cream px-4 py-3.5 flex items-center gap-4 rounded-xl transition-all cursor-pointer">
            <span class="material-symbols-outlined text-xl">settings</span>
            <span class="text-base font-medium tracking-wide font-headline">Configuración</span>
        </a>"""

nav_support = """        <a id="nav-support" class="text-cream/50 hover:bg-cream/5 hover:text-cream px-4 py-3.5 flex items-center gap-4 rounded-xl transition-all cursor-pointer">
            <span class="material-symbols-outlined text-xl">support_agent</span>
            <span class="text-base font-medium tracking-wide font-headline">Soporte y Ayuda</span>
        </a>"""

if "id=\"nav-support\"" not in html:
    html = html.replace(nav_config, nav_config + "\n" + nav_support)

# Add support-view container before closing form/main tag.
support_view = """
    <!-- SUPPORT VIEW -->
    <div id="support-view" class="hidden w-full animate-in fade-in slide-in-from-bottom-4 duration-700 pb-20">
        <div class="mb-12">
            <h2 class="text-3xl font-medium text-cream tracking-wide mt-2 font-headline">Soporte y Ayuda</h2>
            <p class="text-sm font-body text-cream/70 mt-2 max-w-2xl">Manual de usuario y canales de asistencia técnica del sistema.</p>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <!-- Contact Info -->
            <div class="col-span-1 flex flex-col gap-6">
                <div class="glass-panel-premium rounded-3xl p-8 border-t-4 border-accent">
                    <h3 class="text-xl font-headline font-bold text-cream mb-6 flex items-center gap-2">
                        <span class="material-symbols-outlined text-accent">headset_mic</span>
                        Mesa de Ayuda
                    </h3>
                    <div class="space-y-6 text-sm">
                        <div>
                            <p class="text-cream/50 uppercase tracking-widest text-[10px] font-bold mb-1">Horario de Atención</p>
                            <p class="text-cream font-medium">Lunes a Viernes, 8:00 AM - 6:00 PM</p>
                        </div>
                        <div>
                            <p class="text-cream/50 uppercase tracking-widest text-[10px] font-bold mb-1">Correo Electrónico</p>
                            <a href="mailto:soporte@scoreia.com" class="text-accent hover:underline font-medium">soporte@scoreia.com</a>
                        </div>
                        <div>
                            <p class="text-cream/50 uppercase tracking-widest text-[10px] font-bold mb-1">Línea de Emergencia (Caídas)</p>
                            <p class="text-cream font-medium">+58 800-SCOREIA</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- User Manual -->
            <div class="col-span-1 lg:col-span-2">
                <div class="glass-panel-premium rounded-3xl p-8">
                    <h3 class="text-xl font-headline font-bold text-cream mb-6 flex items-center gap-2">
                        <span class="material-symbols-outlined text-accent">menu_book</span>
                        Manual de Usuario Rápido
                    </h3>
                    
                    <div class="space-y-4">
                        <!-- Accordion 1 -->
                        <div class="border border-cream/10 rounded-xl bg-black/20 p-4">
                            <h4 class="font-bold text-cream flex items-center gap-2 mb-2">
                                <span class="material-symbols-outlined text-accent text-sm">analytics</span>
                                1. Generar un Análisis
                            </h4>
                            <p class="text-sm text-cream/70 leading-relaxed">
                                Ve al "Análisis Crediticio", llena los campos de los datos del cliente (incluyendo nombre, apellido y parámetros crediticios). Presiona "Evaluar" para que el modelo predictivo genere la Probabilidad de Incumplimiento y la decisión sugerida.
                            </p>
                        </div>

                        <!-- Accordion 2 -->
                        <div class="border border-cream/10 rounded-xl bg-black/20 p-4">
                            <h4 class="font-bold text-cream flex items-center gap-2 mb-2">
                                <span class="material-symbols-outlined text-accent text-sm">tune</span>
                                2. Uso del Simulador (What-If)
                            </h4>
                            <p class="text-sm text-cream/70 leading-relaxed">
                                Una vez obtenido el resultado, puedes ajustar el "Monto Solicitado" y el "Plazo" con los deslizadores del panel inferior. Esto recalcula la evaluación en tiempo real sin tener que recargar la página, ideal para proponer condiciones alternativas a un cliente rechazado.
                            </p>
                        </div>

                        <!-- Accordion 3 -->
                        <div class="border border-cream/10 rounded-xl bg-black/20 p-4">
                            <h4 class="font-bold text-cream flex items-center gap-2 mb-2">
                                <span class="material-symbols-outlined text-accent text-sm">waterfall_chart</span>
                                3. Gráfico SHAP
                            </h4>
                            <p class="text-sm text-cream/70 leading-relaxed">
                                El gráfico explica cómo llegó el modelo a la decisión. Las barras rojas (+) indican factores que incrementaron el riesgo del cliente, mientras que las barras verdes (-) indican factores positivos que bajaron el riesgo.
                            </p>
                        </div>

                        <!-- Accordion 4 -->
                        <div class="border border-cream/10 rounded-xl bg-black/20 p-4">
                            <h4 class="font-bold text-cream flex items-center gap-2 mb-2">
                                <span class="material-symbols-outlined text-accent text-sm">history</span>
                                4. Auditoría y Reportes Históricos
                            </h4>
                            <p class="text-sm text-cream/70 leading-relaxed">
                                En la pestaña "Historial" queda el rastro de todas las evaluaciones, marcadas con el nombre del analista y fecha. Puedes pulsar "Ver Análisis" para viajar en el tiempo a una evaluación pasada y desde allí "Exportar a PDF" el reporte oficial.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
"""

# Insert support_view just before dashboard-view
if "id=\"support-view\"" not in html:
    html = html.replace('<div id="dashboard-view"', support_view + '\n    <div id="dashboard-view"')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print("Updated app.html with support view")

# Update app.js
js_path = r'app\ui\app.js'
with open(js_path, 'r', encoding='utf-8') as f:
    js = f.read()

# Add DOM elements
if "const navSupport =" not in js:
    js = js.replace("const navConfig = document.getElementById('nav-config');", "const navConfig = document.getElementById('nav-config');\n    const navSupport = document.getElementById('nav-support');")
    js = js.replace("const configView = document.getElementById('config-view');", "const configView = document.getElementById('config-view');\n    const supportView = document.getElementById('support-view');")

# Update navigation routing listener
old_nav_condition = "if (navEval && navHistory && navDashboard && navConfig) {"
new_nav_condition = "if (navEval && navHistory && navDashboard && navConfig && navSupport) {"
if old_nav_condition in js:
    js = js.replace(old_nav_condition, new_nav_condition)

old_nav_listeners = """        navConfig.addEventListener('click', () => {
            setActiveNav(navConfig, configView);
            syncConfigUI();
        });
    }"""
new_nav_listeners = """        navConfig.addEventListener('click', () => {
            setActiveNav(navConfig, configView);
            syncConfigUI();
        });
        navSupport.addEventListener('click', () => {
            setActiveNav(navSupport, supportView);
        });
    }"""
if "navSupport.addEventListener" not in js:
    js = js.replace(old_nav_listeners, new_nav_listeners)

# Update view array in setActiveNav
old_views = "[evalView, historyView, dashboardView, configView].forEach(view => {"
new_views = "[evalView, historyView, dashboardView, configView, supportView].forEach(view => {"
if old_views in js:
    js = js.replace(old_views, new_views)

old_navs = "[navEval, navHistory, navDashboard, navConfig].forEach(nav => {"
new_navs = "[navEval, navHistory, navDashboard, navConfig, navSupport].forEach(nav => {"
if old_navs in js:
    js = js.replace(old_navs, new_navs)

with open(js_path, 'w', encoding='utf-8') as f:
    f.write(js)
print("Updated app.js")
