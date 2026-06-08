import os
import re

files = ['login.html', 'app.html', 'reset_password.html']
base_dir = r'app\ui'

for fname in files:
    filepath = os.path.join(base_dir, fname)
    if not os.path.exists(filepath):
        continue
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # The bad particle code block inside the large script looks like:
    # // --- Particle System (Igual que index.html) ---
    # const canvas = document.getElementById('particleCanvas');
    # ... up to just before // --- Carrusel de Información --- or end of script
    
    # Let's use regex to remove it
    bad_pattern = r'// --- Particle System.*?drawParticles\(\);\s*'
    new_content = re.sub(bad_pattern, '', content, flags=re.DOTALL)
    
    if new_content != content:
        print(f"Removed bad particle script from {fname}")
        content = new_content

    # Also apply the mouse interaction to the dynamic particle script if missing
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
        print(f"Added mouse interaction to {fname}")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

