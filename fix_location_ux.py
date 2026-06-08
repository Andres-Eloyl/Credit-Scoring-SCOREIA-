import re
import os

filepath = r'app\ui\login.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

new_js = """    // --- Location Fetching API ---
    async function fetchCountries() {
        try {
            const res = await fetch('https://restcountries.com/v3.1/all?fields=name,translations');
            const data = await res.json();
            
            let countries = data.map(c => ({
                es: c.translations.spa ? c.translations.spa.common : c.name.common,
                en: c.name.common
            })).sort((a, b) => a.es.localeCompare(b.es));
            
            const select = document.getElementById('regCountry');
            select.innerHTML = '<option value="" disabled selected class="bg-background">Selecciona un país</option>';
            
            countries.forEach(c => {
                select.innerHTML += `<option value="${c.en}" class="bg-background text-cream">${c.es}</option>`;
            });
        } catch(e) {
            console.error(e);
            document.getElementById('regCountry').innerHTML = '<option value="" disabled selected class="bg-background">Error al cargar</option>';
        }
    }

    function convertToInput(id, placeholder) {
        const select = document.getElementById(id);
        if(select && select.tagName === 'SELECT') {
            const input = document.createElement('input');
            input.id = id;
            input.type = 'text';
            input.placeholder = placeholder;
            input.required = true;
            input.className = "w-full bg-transparent border-none px-3 py-3.5 text-cream placeholder-cream/30 focus:outline-none focus:ring-0 font-body-md";
            if(id === 'regState') {
                input.oninput = () => convertToInput('regCity', 'Ej: Ciudad o Municipio');
            }
            select.parentNode.replaceChild(input, select);
            return input;
        }
        return select;
    }

    function convertToSelect(id, defaultText) {
        const el = document.getElementById(id);
        if(el && el.tagName === 'INPUT') {
            const select = document.createElement('select');
            select.id = id;
            select.required = true;
            select.className = "w-full bg-transparent border-none px-3 py-3.5 text-cream focus:text-cream focus:outline-none focus:ring-0 font-body-md";
            if(id === 'regState') {
                select.onchange = fetchCities;
            }
            select.innerHTML = `<option value="" disabled selected class="bg-background">${defaultText}</option>`;
            el.parentNode.replaceChild(select, el);
            return select;
        }
        return el;
    }

    async function fetchStates() {
        const country = document.getElementById('regCountry').value;
        let select = convertToSelect('regState', 'Cargando estados...');
        let citySelect = convertToSelect('regCity', 'Selecciona un estado primero');
        
        select.disabled = true;
        citySelect.disabled = true;
        
        try {
            const res = await fetch('https://countriesnow.space/api/v0.1/countries/states', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ country })
            });
            const json = await res.json();
            
            if(json.data && json.data.states && json.data.states.length > 0) {
                select.innerHTML = '<option value="" disabled selected class="bg-background">Selecciona un estado</option>';
                json.data.states.forEach(s => {
                    select.innerHTML += `<option value="${s.name}" class="bg-background text-cream">${s.name}</option>`;
                });
                select.disabled = false;
            } else {
                convertToInput('regState', 'Ej: Estado o Provincia');
                convertToInput('regCity', 'Ej: Ciudad o Municipio');
            }
        } catch(e) {
            console.error(e);
            convertToInput('regState', 'Ej: Estado o Provincia');
            convertToInput('regCity', 'Ej: Ciudad o Municipio');
        }
    }

    async function fetchCities() {
        const country = document.getElementById('regCountry').value;
        const stateEl = document.getElementById('regState');
        const state = stateEl.value;
        
        if(stateEl.tagName === 'INPUT') {
            convertToInput('regCity', 'Ej: Ciudad o Municipio');
            return;
        }

        let select = convertToSelect('regCity', 'Cargando ciudades...');
        select.disabled = true;
        
        try {
            const res = await fetch('https://countriesnow.space/api/v0.1/countries/state/cities', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ country, state })
            });
            const json = await res.json();
            
            if(json.data && json.data.length > 0) {
                select.innerHTML = '<option value="" disabled selected class="bg-background">Selecciona una ciudad</option>';
                json.data.forEach(c => {
                    select.innerHTML += `<option value="${c}" class="bg-background text-cream">${c}</option>`;
                });
                select.disabled = false;
            } else {
                convertToInput('regCity', 'Ej: Ciudad o Municipio');
            }
        } catch(e) {
            console.error(e);
            convertToInput('regCity', 'Ej: Ciudad o Municipio');
        }
    }

    // Inicializar países al cargar el panel de registro"""

# Regex to replace everything from Location Fetching API to just before the listener
pattern = r'// --- Location Fetching API ---.*?// Inicializar países al cargar el panel de registro'

new_content = re.sub(pattern, new_js, content, flags=re.DOTALL)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Updated login.html UX!")
