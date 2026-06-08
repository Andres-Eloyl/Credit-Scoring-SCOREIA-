import os
import re

html_path = r'app\ui\app.html'
with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Add nav-history
nav_dashboard_line = '<a id="nav-dashboard" class="text-cream/50 hover:bg-cream/5 hover:text-cream px-4 py-3.5 flex items-center gap-4 rounded-xl transition-all cursor-pointer">'
nav_history_block = """        <a id="nav-history" class="text-cream/50 hover:bg-cream/5 hover:text-cream px-4 py-3.5 flex items-center gap-4 rounded-xl transition-all cursor-pointer">
            <span class="material-symbols-outlined text-xl" style="font-variation-settings: 'FILL' 1;">history</span>
            <span class="text-base font-medium tracking-wide font-headline">Historial</span>
        </a>
"""
html = html.replace(nav_dashboard_line, nav_history_block + nav_dashboard_line)

# 2. Remove btnHistory
btn_history_regex = r'<button id="btnHistory".*?</button>'
html = re.sub(btn_history_regex, '', html, flags=re.DOTALL)

# 3. Replace historyModal with history-view
modal_regex = r'<div id="historyModal".*?<!--'
history_view_html = """<div id="history-view" class="hidden w-full animate-in fade-in slide-in-from-bottom-4 duration-700 pb-20">
        <div class="mb-12">
            <h2 class="text-3xl font-medium text-cream tracking-wide mt-2 font-headline">Historial de Evaluaciones</h2>
            <p class="text-sm font-body text-cream/70 mt-2 max-w-2xl">Registro completo de análisis crediticios y auditoría de decisiones.</p>
        </div>

        <div class="glass-panel-premium rounded-3xl p-8 flex flex-col">
            <div class="overflow-x-auto custom-scrollbar pb-4">
                <table class="w-full text-left text-sm text-cream/80 min-w-[800px]">
                    <thead class="text-[10px] uppercase tracking-widest text-cream/40 border-b border-cream/10">
                        <tr>
                            <th class="pb-3 font-bold pl-4">Analista</th>
                            <th class="pb-3 font-bold">Cédula Cliente</th>
                            <th class="pb-3 font-bold">Fecha / Hora</th>
                            <th class="pb-3 font-bold text-center">Decisión</th>
                            <th class="pb-3 font-bold text-right pr-4">Acciones</th>
                        </tr>
                    </thead>
                    <tbody id="historyTableBody" class="divide-y divide-cream/5">
                        
                    </tbody>
                </table>
                <div id="historyEmpty" class="py-16 text-center text-cream/40 text-sm hidden">
                    No hay evaluaciones recientes.
                </div>
            </div>
        </div>
    </div> 

    <!--"""
html = re.sub(modal_regex, history_view_html, html, flags=re.DOTALL)

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)
print("Updated app.html")

js_path = r'app\ui\app.js'
with open(js_path, 'r', encoding='utf-8') as f:
    js = f.read()

# 1. Inject viewHistoricalAnalysis and window.historyCache
cache_init = """let latestFormData = null;
    window.historyCache = {};"""
js = js.replace("let latestFormData = null;", cache_init)

view_func = """    window.viewHistoricalAnalysis = function(id) {
        const item = window.historyCache[id];
        if(!item) return;
        
        const reqData = JSON.parse(item.request_data);
        const shapData = JSON.parse(item.shap_data);
        
        latestFormData = reqData;
        
        const resultMock = {
            pd: item.pd_value,
            riesgo: item.riesgo,
            decision: item.decision,
            shap_data: shapData
        };
        
        // Switch to eval view
        setActiveNav(navEval, evalView);
        
        // Display
        displayResults(resultMock, false);
    };"""
js = js.replace("async function fetchHistory() {", view_func + "\n\n    async function fetchHistory() {")

# 2. Update fetchHistory rendering
fetch_regex = r'data\.forEach\(item => \{.*?(?=</script>|\} catch)'
# Wait, regex is risky for large blocks. I'll use string replacement
start_fetch = js.find("data.forEach(item => {")
end_fetch = js.find("historyTableBody.appendChild(tr);", start_fetch)
if start_fetch != -1 and end_fetch != -1:
    old_fetch_loop = js[start_fetch:end_fetch + len("historyTableBody.appendChild(tr);")]
    new_fetch_loop = """data.forEach(item => {
                window.historyCache[item.id] = item;
                const tr = document.createElement('tr');
                tr.className = "hover:bg-cream/5 transition-colors group";
                const isApproved = item.decision === 'Aprobado';
                const dateObj = new Date(item.timestamp + 'Z');
                const dateStr = dateObj.toLocaleString('es-ES', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
                
                tr.innerHTML = `
                    <td class="py-4 pl-4 font-medium text-cream group-hover:text-accent transition-colors">${item.analyst_name || 'Analista'}</td>
                    <td class="py-4 font-mono text-xs opacity-80">${item.client_id}</td>
                    <td class="py-4 text-xs opacity-60">${dateStr}</td>
                    <td class="py-4 text-center">
                        <span class="px-3 py-1 rounded-full text-[10px] font-bold ${isApproved ? 'bg-accent/20 text-accent' : 'bg-error/20 text-error'}">
                            ${item.decision}
                        </span>
                    </td>
                    <td class="py-4 pr-4 text-right">
                        <button onclick="viewHistoricalAnalysis(${item.id})" class="px-3 py-1.5 rounded bg-surface border border-cream/10 text-xs font-medium hover:border-accent hover:text-accent transition-colors">
                            Ver Análisis
                        </button>
                    </td>
                `;
                historyTableBody.appendChild(tr);"""
    js = js.replace(old_fetch_loop, new_fetch_loop)

# 3. Handle navigation
nav_vars = """    const navEval = document.getElementById('nav-eval');
    const navHistory = document.getElementById('nav-history');
    const navDashboard = document.getElementById('nav-dashboard');
    const navConfig = document.getElementById('nav-config');
    const evalView = document.getElementById('eval-view');
    const historyView = document.getElementById('history-view');
    const dashboardView = document.getElementById('dashboard-view');
    const configView = document.getElementById('config-view');"""

old_nav_vars = """    const navEval = document.getElementById('nav-eval');
    const navDashboard = document.getElementById('nav-dashboard');
    const navConfig = document.getElementById('nav-config');
    const evalView = document.getElementById('eval-view');
    const dashboardView = document.getElementById('dashboard-view');
    const configView = document.getElementById('config-view');"""

js = js.replace(old_nav_vars, nav_vars)

set_active_old = """[navEval, navDashboard, navConfig].forEach(nav => {"""
set_active_new = """[navEval, navHistory, navDashboard, navConfig].forEach(nav => {"""
js = js.replace(set_active_old, set_active_new)

set_view_old = """[evalView, dashboardView, configView].forEach(view => {"""
set_view_new = """[evalView, historyView, dashboardView, configView].forEach(view => {"""
js = js.replace(set_view_old, set_view_new)

nav_listeners_old = """    if (navEval && navDashboard && navConfig) {
        navEval.addEventListener('click', () => setActiveNav(navEval, evalView));
        navDashboard.addEventListener('click', () => {"""
nav_listeners_new = """    if (navEval && navHistory && navDashboard && navConfig) {
        navEval.addEventListener('click', () => setActiveNav(navEval, evalView));
        navHistory.addEventListener('click', () => {
            setActiveNav(navHistory, historyView);
            fetchHistory();
        });
        navDashboard.addEventListener('click', () => {"""
js = js.replace(nav_listeners_old, nav_listeners_new)

# 4. Add analyst_name to payload
payload_old = """        const data = Object.fromEntries(formData.entries());"""
payload_new = """        const data = Object.fromEntries(formData.entries());
        data.analyst_name = localStorage.getItem('scoreia_user') || 'Analista';"""
js = js.replace(payload_old, payload_new)

# Remove old btnHistory listener
btn_hist_regex = r'const btnHistory = document\.getElementById\(\'btnHistory\'\);'
js = re.sub(btn_hist_regex, '', js)

with open(js_path, 'w', encoding='utf-8') as f:
    f.write(js)

print("Updated app.js")
