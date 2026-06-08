import os

# 1. Update index.html logo
index_path = r'app\ui\index.html'
with open(index_path, 'r', encoding='utf-8') as f:
    index_content = f.read()

old_logo = """        <a href="/" class="flex items-center gap-4 group">
            <div class="w-10 h-10 rounded-xl bg-[#0e1410] flex items-center justify-center border border-[#1a261d] transition-all">
                <span class="material-symbols-outlined text-accent text-2xl">blur_on</span>
            </div>
            <span class="text-xl font-headline font-bold text-cream tracking-wide">SCOREIA</span>
        </a>"""

new_logo = """        <a href="/" class="flex items-center gap-3 group">
            <div class="w-10 h-10 rounded-xl bg-surface flex items-center justify-center border border-cream/10 shadow-[0_0_15px_rgba(57,138,72,0.2)] group-hover:shadow-[0_0_20px_rgba(57,138,72,0.4)] transition-shadow">
                <span class="material-symbols-outlined text-accent text-2xl font-bold">blur_on</span>
            </div>
            <div class="flex flex-col justify-center">
                <span class="text-xl font-bold text-cream tracking-wide font-headline leading-tight">SCOREIA</span>
                <span class="text-[9px] font-medium text-cream/50 uppercase tracking-widest mt-0.5">Riesgo Crediticio</span>
            </div>
        </a>"""

index_content = index_content.replace(old_logo, new_logo)

with open(index_path, 'w', encoding='utf-8') as f:
    f.write(index_content)

# 2. Update app.html form fields
app_path = r'app\ui\app.html'
with open(app_path, 'r', encoding='utf-8') as f:
    app_content = f.read()

# ID Cliente -> Cédula de Identidad
app_content = app_content.replace('<label class="premium-label">ID Cliente</label>', '<label class="premium-label">Cédula de Identidad</label>')

# Score Buró -> Puntaje Crediticio
app_content = app_content.replace('<label class="premium-label">Score Buró</label>', '<label class="premium-label">Puntaje Crediticio</label>')

# Typing enhancements
app_content = app_content.replace('<input class="premium-input" type="number" id="edad"', '<input class="premium-input" type="number" min="18" max="100" id="edad"')
app_content = app_content.replace('<input class="premium-input" type="number" step="0.01" id="ingreso_mensual"', '<input class="premium-input" type="number" step="0.01" min="0" id="ingreso_mensual"')
app_content = app_content.replace('<input class="premium-input" type="number" id="antiguedad_laboral"', '<input class="premium-input" type="number" min="0" id="antiguedad_laboral"')
app_content = app_content.replace('<input class="premium-input" type="number" id="score_buro"', '<input class="premium-input" type="number" min="0" max="1000" id="score_buro"')
app_content = app_content.replace('<input class="premium-input" type="number" id="meses_mora_maxima"', '<input class="premium-input" type="number" min="0" id="meses_mora_maxima"')
app_content = app_content.replace('<input class="premium-input" type="number" id="num_creditos_activos"', '<input class="premium-input" type="number" min="0" id="num_creditos_activos"')

with open(app_path, 'w', encoding='utf-8') as f:
    f.write(app_content)

print("Updates completed.")
