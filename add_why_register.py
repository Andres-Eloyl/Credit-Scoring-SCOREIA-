import os

filepath = r'app\ui\login.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

target = '<div class="relative z-10 mt-12 max-w-xl w-full">'
new_section = """
        <!-- Relleno: Por qué es importante -->
        <div class="relative z-10 my-auto py-12 max-w-md animate-hero-delay hidden transition-all duration-700" id="whyRegisterSection">
            <div class="flex items-center gap-3 mb-4">
                <div class="w-8 h-8 rounded-full bg-accent/20 flex items-center justify-center border border-accent/30">
                    <span class="material-symbols-outlined text-accent text-sm">vpn_key</span>
                </div>
                <h3 class="text-xl font-bold font-headline text-cream tracking-wide">¿Por qué es importante el registro?</h3>
            </div>
            <p class="text-cream/60 font-body-md leading-relaxed text-sm pl-11">
                Al crear una cuenta institucional, garantizamos la <strong>trazabilidad y seguridad bancaria</strong> de todas las evaluaciones. 
                <br><br>
                Obtendrás acceso a un entorno privado donde SCOREIA procesa historiales crediticios en tiempo real, generando modelos explicables (XAI) exclusivos para tu departamento.
            </p>
        </div>

        <div class="relative z-10 mt-12 max-w-xl w-full">"""

# Insert the HTML block
if 'whyRegisterSection' not in content:
    content = content.replace(target, new_section, 1)

# Now, we only want this to show when the user clicks "Registrarse".
# Because on the "Login" screen, the height is small, and adding this might cause overflow or look crowded.
# Or wait, the user said "al extender la pagina por el registro". So it's ONLY when the register form is visible!
# We can toggle the 'hidden' class on `whyRegisterSection` when btnShowRegister / btnShowLogin are clicked.

js_register_target = "registerPanel.classList.add('animate-fade-in-up');"
js_register_new = """registerPanel.classList.add('animate-fade-in-up');
        const whySec = document.getElementById('whyRegisterSection');
        if(whySec) { whySec.classList.remove('hidden'); }"""

js_login_target = "loginPanel.classList.add('animate-fade-in-up');"
js_login_new = """loginPanel.classList.add('animate-fade-in-up');
        const whySec = document.getElementById('whyRegisterSection');
        if(whySec) { whySec.classList.add('hidden'); }"""

if "whySec.classList.remove('hidden')" not in content:
    content = content.replace(js_register_target, js_register_new)
    content = content.replace(js_login_target, js_login_new)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Added whyRegisterSection to login.html")
