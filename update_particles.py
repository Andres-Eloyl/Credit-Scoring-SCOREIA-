import os
import re

filepath = r'app\ui\app.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# We need to replace the animateParticles function block
start_idx = content.find("function animateParticles() {")
end_idx = content.find("initParticles();", start_idx)

if start_idx != -1 and end_idx != -1:
    old_block = content[start_idx:end_idx]
    
    new_block = """let currentAccentRgb = '57, 138, 72';
    setInterval(() => {
        const style = getComputedStyle(document.documentElement);
        const val = style.getPropertyValue('--color-accent-comma').trim();
        if (val) currentAccentRgb = val;
    }, 200);

    function animateParticles() {
        requestAnimationFrame(animateParticles);
        ctx.clearRect(0, 0, innerWidth, innerHeight);
        for (let i = 0; i < particlesArray.length; i++) {
            let p = particlesArray[i];
            p.x += p.speedX;
            p.y += p.speedY;
            if (p.x < 0 || p.x > innerWidth) p.speedX *= -1;
            if (p.y < 0 || p.y > innerHeight) p.speedY *= -1;
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(${currentAccentRgb}, 0.5)`;
            ctx.fill();
            let dxMouse = mouse.x - p.x;
            let dyMouse = mouse.y - p.y;
            let distMouse = Math.sqrt(dxMouse*dxMouse + dyMouse*dyMouse);
            if (distMouse < 150) {
                ctx.beginPath();
                ctx.strokeStyle = `rgba(${currentAccentRgb}, ${0.4 - distMouse/500})`;
                ctx.moveTo(p.x, p.y);
                ctx.lineTo(mouse.x, mouse.y);
                ctx.stroke();
            }
            
            for (let j = i; j < particlesArray.length; j++) {
                let p2 = particlesArray[j];
                let dx = p.x - p2.x;
                let dy = p.y - p2.y;
                let distance = Math.sqrt(dx * dx + dy * dy);
                if (distance < 100) {
                    ctx.beginPath();
                    ctx.strokeStyle = `rgba(${currentAccentRgb}, ${0.25 - distance/1000})`;
                    ctx.moveTo(p.x, p.y);
                    ctx.lineTo(p2.x, p2.y);
                    ctx.stroke();
                }
            }
        }
    }

    """
    
    content = content.replace(old_block, new_block)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Updated canvas particles logic in app.html!")
else:
    print("Could not find the animateParticles block.")
