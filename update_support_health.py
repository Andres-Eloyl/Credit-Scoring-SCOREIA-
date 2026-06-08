import os
import re

# 1. Update main_api.py to add /api/health endpoint
api_path = r'app\main_api.py'
with open(api_path, 'r', encoding='utf-8') as f:
    api = f.read()

health_endpoint = """
@app.get("/api/health")
async def health_check(db: Session = Depends(database.get_db)):
    db_status = "error"
    try:
        # Simple query to check db
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except:
        pass
    
    motor_status = "ok" if model else "error"
    
    return {
        "status": "success",
        "motor": motor_status,
        "db": db_status
    }
"""

if "/api/health" not in api:
    api = api.replace("@app.get(\"/api/stats\")", health_endpoint + "\n@app.get(\"/api/stats\")")
    with open(api_path, 'w', encoding='utf-8') as f:
        f.write(api)
    print("Updated main_api.py")

# 2. Update app.html
html_path = r'app\ui\app.html'
with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

# Add Whatsapp
old_line = """                        <div>
                            <p class="text-cream/50 uppercase tracking-widest text-[10px] font-bold mb-1">Línea de Emergencia (Caídas)</p>
                            <p class="text-cream font-medium">+58 800-SCOREIA</p>
                        </div>"""
new_line = """                        <div>
                            <p class="text-cream/50 uppercase tracking-widest text-[10px] font-bold mb-1">Línea de Emergencia (Caídas)</p>
                            <p class="text-cream font-medium">+58 800-SCOREIA</p>
                        </div>
                        <div>
                            <p class="text-cream/50 uppercase tracking-widest text-[10px] font-bold mb-1">WhatsApp Técnico</p>
                            <a href="https://wa.me/584140000000" target="_blank" class="text-accent hover:underline font-medium flex items-center gap-1">
                                +58 414-0000000 <span class="material-symbols-outlined text-[14px]">open_in_new</span>
                            </a>
                        </div>"""
html = html.replace(old_line, new_line)

# Update Status Indicators and Button
old_status = """                    <div class="mt-auto pt-8">
                        <p class="text-cream/50 uppercase tracking-widest text-[10px] font-bold mb-4">Estado del Sistema</p>
                        <div class="space-y-2 mb-6">
                            <div class="flex items-center justify-between bg-black/20 p-3 rounded-xl border border-cream/5">
                                <span class="text-xs text-cream/70 flex items-center gap-2">
                                    <span class="w-2 h-2 rounded-full bg-[#398a48] shadow-[0_0_8px_rgba(57,138,72,0.8)] animate-pulse"></span>
                                    Motor Predictivo
                                </span>
                                <span class="text-xs font-bold text-[#398a48] tracking-widest uppercase">Operativo</span>
                            </div>
                            <div class="flex items-center justify-between bg-black/20 p-3 rounded-xl border border-cream/5">
                                <span class="text-xs text-cream/70 flex items-center gap-2">
                                    <span class="w-2 h-2 rounded-full bg-[#398a48] shadow-[0_0_8px_rgba(57,138,72,0.8)] animate-pulse"></span>
                                    Base de Datos
                                </span>
                                <span class="text-xs font-bold text-[#398a48] tracking-widest uppercase">En Línea</span>
                            </div>
                        </div>
                        
                        <button class="w-full py-3 rounded-xl bg-accent/10 hover:bg-accent/20 border border-accent/20 text-accent font-bold text-xs tracking-wide transition-all flex items-center justify-center gap-2 shadow-md hover:shadow-accent/10" type="button">
                            <span class="material-symbols-outlined text-[16px]">support</span>
                            Generar Ticket de Soporte
                        </button>
                    </div>"""

new_status = """                    <div class="mt-auto pt-8">
                        <p class="text-cream/50 uppercase tracking-widest text-[10px] font-bold mb-4 flex items-center gap-2">
                            Estado del Sistema
                            <span class="material-symbols-outlined text-[12px] animate-spin text-cream/30" id="healthSpinner">sync</span>
                        </p>
                        <div class="space-y-2 mb-6">
                            <div class="flex items-center justify-between bg-black/20 p-3 rounded-xl border border-cream/5">
                                <span class="text-xs text-cream/70 flex items-center gap-2">
                                    <span id="motorDot" class="w-2 h-2 rounded-full bg-cream/20 shadow-none"></span>
                                    Motor Predictivo
                                </span>
                                <span id="motorText" class="text-xs font-bold text-cream/50 tracking-widest uppercase">Conectando...</span>
                            </div>
                            <div class="flex items-center justify-between bg-black/20 p-3 rounded-xl border border-cream/5">
                                <span class="text-xs text-cream/70 flex items-center gap-2">
                                    <span id="dbDot" class="w-2 h-2 rounded-full bg-cream/20 shadow-none"></span>
                                    Base de Datos
                                </span>
                                <span id="dbText" class="text-xs font-bold text-cream/50 tracking-widest uppercase">Conectando...</span>
                            </div>
                        </div>
                        
                        <button id="btnGenerateReport" class="w-full py-3 rounded-xl bg-cream/5 hover:bg-cream/10 border border-cream/10 text-cream font-bold text-xs tracking-wide transition-all flex items-center justify-center gap-2 shadow-md" type="button">
                            <span class="material-symbols-outlined text-[16px]">description</span>
                            Generar Reporte de Diagnóstico
                        </button>
                    </div>"""
html = html.replace(old_status, new_status)

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)
print("Updated app.html")

# 3. Update app.js
js_path = r'app\ui\app.js'
with open(js_path, 'r', encoding='utf-8') as f:
    js = f.read()

health_logic = """
    // --- Health Check & Diagnostics ---
    const motorDot = document.getElementById('motorDot');
    const motorText = document.getElementById('motorText');
    const dbDot = document.getElementById('dbDot');
    const dbText = document.getElementById('dbText');
    const btnGenerateReport = document.getElementById('btnGenerateReport');
    
    let lastHealthStatus = { motor: 'unknown', db: 'unknown' };

    async function checkHealth() {
        if (!motorDot) return;
        try {
            const res = await fetch('/api/health');
            if (res.ok) {
                const data = await res.json();
                lastHealthStatus = data;
                
                if (data.motor === 'ok') {
                    motorDot.className = "w-2 h-2 rounded-full bg-[#398a48] shadow-[0_0_8px_rgba(57,138,72,0.8)] animate-pulse";
                    motorText.className = "text-xs font-bold text-[#398a48] tracking-widest uppercase";
                    motorText.innerText = "Operativo";
                } else {
                    motorDot.className = "w-2 h-2 rounded-full bg-error shadow-[0_0_8px_rgba(239,68,68,0.8)] animate-pulse";
                    motorText.className = "text-xs font-bold text-error tracking-widest uppercase";
                    motorText.innerText = "Error";
                }
                
                if (data.db === 'ok') {
                    dbDot.className = "w-2 h-2 rounded-full bg-[#398a48] shadow-[0_0_8px_rgba(57,138,72,0.8)] animate-pulse";
                    dbText.className = "text-xs font-bold text-[#398a48] tracking-widest uppercase";
                    dbText.innerText = "En Línea";
                } else {
                    dbDot.className = "w-2 h-2 rounded-full bg-error shadow-[0_0_8px_rgba(239,68,68,0.8)] animate-pulse";
                    dbText.className = "text-xs font-bold text-error tracking-widest uppercase";
                    dbText.innerText = "Desconectada";
                }
            }
        } catch(e) {
            motorDot.className = "w-2 h-2 rounded-full bg-error shadow-[0_0_8px_rgba(239,68,68,0.8)] animate-pulse";
            motorText.className = "text-xs font-bold text-error tracking-widest uppercase";
            motorText.innerText = "Fuera de Línea";
            dbDot.className = "w-2 h-2 rounded-full bg-error shadow-[0_0_8px_rgba(239,68,68,0.8)] animate-pulse";
            dbText.className = "text-xs font-bold text-error tracking-widest uppercase";
            dbText.innerText = "Fuera de Línea";
        }
    }
    
    // Check health every 30 seconds
    setInterval(checkHealth, 30000);
    // Initial check
    setTimeout(checkHealth, 1000);

    if (btnGenerateReport) {
        btnGenerateReport.addEventListener('click', () => {
            const dateStr = new Date().toLocaleString('es-ES');
            const ua = navigator.userAgent;
            const content = `===========================================
REPORTE DE DIAGNÓSTICO SCOREIA
===========================================
Fecha de Generación : ${dateStr}
Agente de Usuario   : ${ua}
Pantalla            : ${window.innerWidth}x${window.innerHeight}

ESTADO DE SERVICIOS:
Motor Predictivo    : ${lastHealthStatus.motor.toUpperCase()}
Base de Datos       : ${lastHealthStatus.db.toUpperCase()}

Si experimenta problemas, por favor adjunte 
este archivo al contactar a soporte@scoreia.com
===========================================
`;
            const blob = new Blob([content], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `Diagnostico_SCOREIA_${Date.now()}.txt`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        });
    }
"""

if "btnGenerateReport.addEventListener" not in js:
    js = js + "\n" + health_logic
    with open(js_path, 'w', encoding='utf-8') as f:
        f.write(js)
    print("Updated app.js")
