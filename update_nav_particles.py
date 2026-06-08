import os
import re

files = ['index.html', 'about.html', 'features.html', 'support.html', 'tech.html', 'theory.html', 'use_cases.html', 'app.html', 'login.html', 'reset_password.html']
base_dir = r'app\ui'

for fname in files:
    filepath = os.path.join(base_dir, fname)
    if not os.path.exists(filepath):
        continue
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Add mouse interaction to particle script
    old_particle_inner = """            for (let j = i; j < particlesArray.length; j++) {"""
    
    new_particle_inner = """            let dxMouse = mouse.x - p.x;
            let dyMouse = mouse.y - p.y;
            let distMouse = Math.sqrt(dxMouse*dxMouse + dyMouse*dyMouse);
            if (distMouse < 150) {
                ctx.beginPath();
                ctx.strokeStyle = `rgba(57, 138, 72, ${0.3 - distMouse/500})`;
                ctx.moveTo(p.x, p.y);
                ctx.lineTo(mouse.x, mouse.y);
                ctx.stroke();
            }
            
            for (let j = i; j < particlesArray.length; j++) {"""
    
    if 'dxMouse' not in content:
        content = content.replace(old_particle_inner, new_particle_inner)

    # 2. Update navbar in internal pages
    if fname not in ['index.html', 'app.html', 'login.html', 'reset_password.html']:
        old_nav_acceso = """        <!-- Acceso -->
        <a href="/login" class="flex items-center gap-2 text-[15px] text-cream/70 hover:text-cream transition-colors tracking-wide font-medium">
            <span class="material-symbols-outlined text-xl">login</span>
            Ingresar
        </a>"""
        
        new_nav_acceso = """        <!-- Acceso -->
        <div class="flex items-center gap-6">
            <a href="/" class="flex items-center gap-2 text-[15px] text-cream/70 hover:text-cream transition-colors tracking-wide font-medium">
                <span class="material-symbols-outlined text-xl">home</span>
                Volver al inicio
            </a>
            <a href="/login" class="flex items-center gap-2 text-[15px] text-cream/70 hover:text-cream transition-colors tracking-wide font-medium">
                <span class="material-symbols-outlined text-xl">login</span>
                Ingresar
            </a>
        </div>"""
        
        if 'Volver al inicio' not in content:
            content = content.replace(old_nav_acceso, new_nav_acceso)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'Updated {fname}')
