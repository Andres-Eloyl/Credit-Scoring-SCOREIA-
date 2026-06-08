import os
import glob

# 1. Fix app.js instant apply
app_js_path = r'app\ui\app.js'
with open(app_js_path, 'r', encoding='utf-8') as f:
    js_content = f.read()

old_click = """            btn.addEventListener('click', (e) => {
                currentConfig.accentColor = e.target.dataset.color;

                colorBtns.forEach(b => b.classList.remove('ring-2', 'ring-white', 'ring-offset-2', 'ring-offset-[#1e211d]'));

                e.target.classList.add('ring-2', 'ring-white', 'ring-offset-2', 'ring-offset-[#1e211d]');
            });"""

new_click = """            btn.addEventListener('click', (e) => {
                currentConfig.accentColor = e.target.dataset.color;

                colorBtns.forEach(b => b.classList.remove('ring-2', 'ring-white', 'ring-offset-2', 'ring-offset-[#1e211d]'));

                e.target.classList.add('ring-2', 'ring-white', 'ring-offset-2', 'ring-offset-[#1e211d]');
                
                // Apply instantly without reloading or saving
                applyThemeConfig();
            });"""

if old_click in js_content:
    js_content = js_content.replace(old_click, new_click)
    with open(app_js_path, 'w', encoding='utf-8') as f:
        f.write(js_content)
    print("Fixed instant color apply in app.js")
else:
    print("Could not find the colorBtns click listener in app.js")

# 2. Revert canvas particles in all HTML files EXCEPT app.html to use hardcoded green
base_dir = r'app\ui'
html_files = glob.glob(os.path.join(base_dir, '*.html'))

for filepath in html_files:
    if os.path.basename(filepath) == 'app.html':
        continue # app.html uses currentAccentRgb, it's fine.
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Revert the specific canvas lines
    if "rgba(var(--color-accent-comma)," in content:
        # We only want to replace it inside <script> tags. But the string `rgba(var(--color-accent-comma), ${` is uniquely used in canvas template literals!
        content = content.replace("`rgba(var(--color-accent-comma), ${", "`rgba(57, 138, 72, ${")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Reverted canvas color to green in {os.path.basename(filepath)}")

print("All fixes applied!")
