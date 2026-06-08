import re
import os

filepath = r'app\ui\login.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Fix phone code width and padding
old_phone = 'select id="regCountryCode" required onchange="updateFlagIcon()" class="bg-transparent border-none py-3.5 pl-2 pr-1 text-cream/60 focus:text-cream focus:outline-none focus:ring-0 font-body-md w-[100px]"'
new_phone = 'select id="regCountryCode" required onchange="updateFlagIcon()" class="bg-transparent border-none py-3.5 pl-2 pr-6 text-cream/60 focus:text-cream focus:outline-none focus:ring-0 font-body-md w-[120px]"'
content = content.replace(old_phone, new_phone)

# 2. Replace Country input with select
old_country = """<input id="regCountry" type="text" placeholder="Ej: Venezuela" required
                            class="w-full bg-transparent border-none px-3 py-3.5 text-cream placeholder-cream/30 focus:outline-none focus:ring-0 font-body-md">"""
new_country = """<select id="regCountry" required onchange="fetchStates()"
                            class="w-full bg-transparent border-none px-3 py-3.5 text-cream focus:text-cream focus:outline-none focus:ring-0 font-body-md">
                            <option value="" disabled selected class="bg-background">Cargando países...</option>
                        </select>"""
content = content.replace(old_country, new_country)

# 3. Replace State input with select
old_state = """<input id="regState" type="text" placeholder="Ej: Distrito Capital" required
                            class="w-full bg-transparent border-none px-3 py-3.5 text-cream placeholder-cream/30 focus:outline-none focus:ring-0 font-body-md">"""
new_state = """<select id="regState" required onchange="fetchCities()" disabled
                            class="w-full bg-transparent border-none px-3 py-3.5 text-cream focus:text-cream focus:outline-none focus:ring-0 font-body-md">
                            <option value="" disabled selected class="bg-background">Selecciona un país primero</option>
                        </select>"""
content = content.replace(old_state, new_state)

# 4. Replace City input with select
old_city = """<input id="regCity" type="text" placeholder="Ej: Caracas" required
                            class="w-full bg-transparent border-none px-3 py-3.5 text-cream placeholder-cream/30 focus:outline-none focus:ring-0 font-body-md">"""
new_city = """<select id="regCity" required disabled
                            class="w-full bg-transparent border-none px-3 py-3.5 text-cream focus:text-cream focus:outline-none focus:ring-0 font-body-md">
                            <option value="" disabled selected class="bg-background">Selecciona un estado primero</option>
                        </select>"""
content = content.replace(old_city, new_city)

# 5. Add JS to fetch locations
location_js = """
    // --- Location Fetching API ---
    async function fetchCountries() {
        try {
            const res = await fetch('https://countriesnow.space/api/v0.1/countries/positions');
            const json = await res.json();
            const select = document.getElementById('regCountry');
            select.innerHTML = '<option value="" disabled selected class="bg-background">Selecciona un país</option>';
            // Ordenar alfabeticamente
            const countries = json.data.sort((a,b) => a.name.localeCompare(b.name));
            countries.forEach(c => {
                select.innerHTML += `<option value="${c.name}" class="bg-background text-cream">${c.name}</option>`;
            });
        } catch(e) {
            console.error(e);
            document.getElementById('regCountry').innerHTML = '<option value="" disabled selected class="bg-background">Error al cargar</option>';
        }
    }

    async function fetchStates() {
        const country = document.getElementById('regCountry').value;
        const select = document.getElementById('regState');
        const citySelect = document.getElementById('regCity');
        select.disabled = true;
        select.innerHTML = '<option value="" disabled selected class="bg-background">Cargando estados...</option>';
        citySelect.innerHTML = '<option value="" disabled selected class="bg-background">Selecciona un estado primero</option>';
        citySelect.disabled = true;
        
        try {
            const res = await fetch('https://countriesnow.space/api/v0.1/countries/states', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ country })
            });
            const json = await res.json();
            select.innerHTML = '<option value="" disabled selected class="bg-background">Selecciona un estado</option>';
            if(json.data && json.data.states && json.data.states.length > 0) {
                json.data.states.forEach(s => {
                    select.innerHTML += `<option value="${s.name}" class="bg-background text-cream">${s.name}</option>`;
                });
                select.disabled = false;
            } else {
                select.innerHTML = '<option value="N/A" class="bg-background text-cream">No aplica / No hay datos</option>';
                select.disabled = false;
                select.value = 'N/A';
                fetchCities(); // Intentar cargar ciudades si no hay estados
            }
        } catch(e) {
            console.error(e);
            select.innerHTML = '<option value="Manual" class="bg-background text-cream">Error al cargar</option>';
            select.disabled = false;
        }
    }

    async function fetchCities() {
        const country = document.getElementById('regCountry').value;
        const state = document.getElementById('regState').value;
        const select = document.getElementById('regCity');
        select.disabled = true;
        select.innerHTML = '<option value="" disabled selected class="bg-background">Cargando ciudades...</option>';
        
        try {
            // Si el estado es N/A, algunas APIs fallan al buscar ciudades.
            const body = state === 'N/A' ? { country } : { country, state };
            const res = await fetch('https://countriesnow.space/api/v0.1/countries/state/cities', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });
            const json = await res.json();
            select.innerHTML = '<option value="" disabled selected class="bg-background">Selecciona una ciudad</option>';
            if(json.data && json.data.length > 0) {
                json.data.forEach(c => {
                    select.innerHTML += `<option value="${c}" class="bg-background text-cream">${c}</option>`;
                });
                select.disabled = false;
            } else {
                select.innerHTML = '<option value="N/A" class="bg-background text-cream">No hay datos</option>';
                select.disabled = false;
                select.value = 'N/A';
            }
        } catch(e) {
            console.error(e);
            select.innerHTML = '<option value="Manual" class="bg-background text-cream">No hay datos</option>';
            select.disabled = false;
        }
    }

    // Inicializar países al cargar el panel de registro
    btnShowRegister.addEventListener('click', (e) => {
        // ... (existing code handles animation) ...
        // Only load if not already loaded
        if(document.getElementById('regCountry').options.length <= 1) {
            fetchCountries();
        }
    });
"""

# Insert location JS before the closing script tag of the logic block
if 'fetchCountries()' not in content:
    content = content.replace('btnShowRegister.addEventListener(\'click\', (e) => {', location_js + '\n    btnShowRegister.addEventListener(\'click\', (e) => {')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated login.html")
