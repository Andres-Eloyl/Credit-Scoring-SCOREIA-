import os

files_to_edit = ['index.html', 'about.html', 'features.html', 'support.html', 'tech.html', 'theory.html', 'use_cases.html']
base_dir = r'app\ui'

nav_index = """
<!-- NAV -->
<nav class="fixed top-0 left-0 w-full z-50 bg-surface/60 backdrop-blur-3xl border-b border-cream/10">
    <div class="w-full px-8 xl:px-12 h-20 flex items-center justify-between">
        <!-- Logo -->
        <a href="/" class="flex items-center gap-4 group">
            <div class="w-10 h-10 rounded-xl bg-[#0e1410] flex items-center justify-center border border-[#1a261d] transition-all">
                <span class="material-symbols-outlined text-accent text-2xl">blur_on</span>
            </div>
            <span class="text-xl font-headline font-bold text-cream tracking-wide">SCOREIA</span>
        </a>
        
        <!-- Links Centro -->
        <div class="hidden lg:flex items-center gap-10">
            <a href="/funcionalidades" class="text-[15px] text-cream/70 hover:text-cream transition-colors tracking-wide font-medium">Funcionalidades</a>
            <a href="/tecnologia" class="text-[15px] text-cream/70 hover:text-cream transition-colors tracking-wide font-medium">Tecnología</a>
            <a href="/casos-de-uso" class="text-[15px] text-cream/70 hover:text-cream transition-colors tracking-wide font-medium">Casos de Uso</a>
            <a href="/acerca-de" class="text-[15px] text-cream/70 hover:text-cream transition-colors tracking-wide font-medium">Acerca de</a>
            <a href="/soporte" class="text-[15px] text-cream/70 hover:text-cream transition-colors tracking-wide font-medium">Soporte</a>
        </div>

        <!-- Acceso -->
        <a href="/login" class="flex items-center gap-2 text-[15px] text-cream/70 hover:text-cream transition-colors tracking-wide font-medium">
            <span class="material-symbols-outlined text-xl">login</span>
            Ingresar
        </a>
    </div>
</nav>
"""

nav_inner = """
<!-- NAV -->
<nav class="fixed top-0 left-0 w-full z-50 bg-surface/60 backdrop-blur-3xl border-b border-cream/10">
    <div class="w-full px-8 xl:px-12 h-20 flex items-center justify-between">
        <!-- Logo -->
        <a href="/" class="flex items-center gap-4 group">
            <div class="w-10 h-10 rounded-xl bg-[#0e1410] flex items-center justify-center border border-[#1a261d] transition-all">
                <span class="material-symbols-outlined text-accent text-2xl">blur_on</span>
            </div>
            <span class="text-xl font-headline font-bold text-cream tracking-wide">SCOREIA</span>
        </a>
        
        <!-- Links Centro -->
        <div class="hidden lg:flex items-center gap-10">
            <a href="/funcionalidades" class="text-[15px] text-cream/70 hover:text-cream transition-colors tracking-wide font-medium">Funcionalidades</a>
            <a href="/tecnologia" class="text-[15px] text-cream/70 hover:text-cream transition-colors tracking-wide font-medium">Tecnología</a>
            <a href="/casos-de-uso" class="text-[15px] text-cream/70 hover:text-cream transition-colors tracking-wide font-medium">Casos de Uso</a>
            <a href="/acerca-de" class="text-[15px] text-cream/70 hover:text-cream transition-colors tracking-wide font-medium">Acerca de</a>
            <a href="/soporte" class="text-[15px] text-cream/70 hover:text-cream transition-colors tracking-wide font-medium">Soporte</a>
        </div>

        <!-- Acceso -->
        <a href="/" class="flex items-center gap-2 text-[15px] text-cream/70 hover:text-cream transition-colors tracking-wide font-medium">
            <span class="material-symbols-outlined text-xl">home</span>
            Volver al inicio
        </a>
    </div>
</nav>
"""

for fname in files_to_edit:
    filepath = os.path.join(base_dir, fname)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    target = '<div class="grid-overlay"></div>'
    if target in content:
        # Check if already added
        if '<!-- NAV -->' not in content:
            nav = nav_index if fname == 'index.html' else nav_inner
            content = content.replace(target, target + '\n' + nav)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f'Added nav to {fname}')
        else:
            print(f'{fname} already has nav')
    else:
        print(f'Could not find target in {fname}')
