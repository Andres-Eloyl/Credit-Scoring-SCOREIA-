import os

filepath = r'app\ui\app.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old_sidebar = """            <div>
                <h1 class="text-lg font-headline font-medium text-cream tracking-wide tracking-tight">SCOREIA</h1>
            </div>"""

new_sidebar = """            <div class="flex flex-col">
                <h1 class="text-lg font-headline font-medium text-cream tracking-wide tracking-tight leading-tight">SCOREIA</h1>
                <div class="text-[9px] font-medium text-cream/50 uppercase tracking-widest">Riesgo Crediticio</div>
            </div>"""

if old_sidebar in content:
    content = content.replace(old_sidebar, new_sidebar)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
        print("Updated app.html sidebar")
else:
    print("Already updated or not found")
