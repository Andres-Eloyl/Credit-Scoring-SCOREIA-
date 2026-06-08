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

    # 1. In index.html, remove the bad script that causes SyntaxError
    if fname in ['index.html', 'app.html', 'login.html']:
        content = re.sub(r'<script>\s*const canvas = document.getElementById\(\'particleCanvas\'\);.*?</script>\s*', '', content, flags=re.DOTALL)

    # 2. In all files, change z-index of the dynamically created canvas from -2 to 0
    # so it actually shows up above the opaque bg-mesh (which is -1)
    content = content.replace("canvas.style.zIndex = '-2';", "canvas.style.zIndex = '0';")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'Fixed particles in {fname}')
