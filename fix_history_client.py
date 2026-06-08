import os
import re

# 1. Delete DB
db_path = r'data\scoreia.db'
if os.path.exists(db_path):
    os.remove(db_path)
    print("Deleted scoreia.db")

# 2. Update models.py
models_path = r'app\models.py'
with open(models_path, 'r', encoding='utf-8') as f:
    models = f.read()

models = models.replace("analyst_name = Column(String, index=True)", "client_name = Column(String, index=True)")

with open(models_path, 'w', encoding='utf-8') as f:
    f.write(models)
print("Updated models.py")

# 3. Update main_api.py
api_path = r'app\main_api.py'
with open(api_path, 'r', encoding='utf-8') as f:
    api = f.read()

api = api.replace("analyst_name=data.get(\"analyst_name\", \"Analista\")", "client_name=data.get(\"client_name\", \"Sin Nombre\")")

with open(api_path, 'w', encoding='utf-8') as f:
    f.write(api)
print("Updated main_api.py")

# 4. Update app.html
html_path = r'app\ui\app.html'
with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

# Replace table header "Analista" with "Nombre del Cliente"
html = html.replace('<th class="pb-3 font-bold pl-4">Analista</th>', '<th class="pb-3 font-bold pl-4">Nombre del Cliente</th>')

# Insert client_name input before client_id
old_client_id_div = """                    <div class="space-y-1">
                        <label class="block text-[11px] font-bold text-cream/70 uppercase tracking-widest mb-1">Cédula de Identidad</label>
                        <input class="premium-input" type="text" id="client_id" name="client_id" autocomplete="new-password" placeholder="Ej: 12345678" oninput="let v = this.value.replace(/[^0-9]/g, ''); this.value = v.slice(0, 8);" onchange="let v = this.value.replace(/[^0-9]/g, ''); this.value = v.slice(0, 8);" required/>
                    </div>"""

new_client_fields = """                    <div class="space-y-1">
                        <label class="block text-[11px] font-bold text-cream/70 uppercase tracking-widest mb-1">Nombre del Cliente</label>
                        <input class="premium-input" type="text" id="client_name" name="client_name" placeholder="Ej: Juan Pérez" required/>
                    </div>
                    <div class="space-y-1">
                        <label class="block text-[11px] font-bold text-cream/70 uppercase tracking-widest mb-1">Cédula de Identidad</label>
                        <input class="premium-input" type="text" id="client_id" name="client_id" autocomplete="new-password" placeholder="Ej: 12345678" oninput="let v = this.value.replace(/[^0-9]/g, ''); this.value = v.slice(0, 8);" onchange="let v = this.value.replace(/[^0-9]/g, ''); this.value = v.slice(0, 8);" required/>
                    </div>"""

html = html.replace(old_client_id_div, new_client_fields)

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)
print("Updated app.html")

# 5. Update app.js
js_path = r'app\ui\app.js'
with open(js_path, 'r', encoding='utf-8') as f:
    js = f.read()

# Remove C- from Dummy
js = js.replace('client_id: "C-" + randomInt(10000, 99999),', 'client_id: String(randomInt(10000000, 29999999)),\n            client_name: "Cliente Prueba " + randomInt(1, 999),')

# Update dummy population loop to include client_name
# The loop automatically iterates over dummyData keys, so we just need to add client_name to dummyData.

# Update History table row
old_td = "<td class=\"py-4 pl-4 font-medium text-cream group-hover:text-accent transition-colors\">${item.analyst_name || 'Analista'}</td>"
new_td = "<td class=\"py-4 pl-4 font-medium text-cream group-hover:text-accent transition-colors\">${item.client_name || 'Sin Nombre'}</td>"
js = js.replace(old_td, new_td)

# Remove analyst_name payload injection
js = js.replace("data.analyst_name = localStorage.getItem('scoreia_user') || 'Analista';", "")

# Update PDF generator to use client_name if available
pdf_old = "pdfClientId.innerText = latestFormData.client_id || 'N/A';"
pdf_new = "pdfClientId.innerText = (latestFormData.client_name ? latestFormData.client_name + ' (V-' + latestFormData.client_id + ')' : latestFormData.client_id) || 'N/A';"
js = js.replace(pdf_old, pdf_new)

with open(js_path, 'w', encoding='utf-8') as f:
    f.write(js)
print("Updated app.js")
