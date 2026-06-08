import os

files = ['index.html', 'about.html', 'features.html', 'support.html', 'tech.html', 'theory.html', 'use_cases.html']
base_dir = r'app\ui'

# 1. Update Navigation Bars in all main pages
old_nav_logo = """        <!-- Logo -->
        <a href="/" class="flex items-center gap-3 group">
            <div class="w-10 h-10 rounded-xl bg-surface flex items-center justify-center border border-cream/10 shadow-[0_0_15px_rgba(57,138,72,0.2)] group-hover:shadow-[0_0_20px_rgba(57,138,72,0.4)] transition-shadow">
                <span class="material-symbols-outlined text-accent text-2xl font-bold">blur_on</span>
            </div>
            <h1 class="text-xl font-bold text-cream tracking-wide font-headline">SCOREIA</h1>
        </a>"""

new_nav_logo = """        <!-- Logo -->
        <a href="/" class="flex items-center gap-3 group">
            <div class="w-10 h-10 rounded-xl bg-surface flex items-center justify-center border border-cream/10 shadow-[0_0_15px_rgba(57,138,72,0.2)] group-hover:shadow-[0_0_20px_rgba(57,138,72,0.4)] transition-shadow">
                <span class="material-symbols-outlined text-accent text-2xl font-bold">blur_on</span>
            </div>
            <div class="flex flex-col">
                <h1 class="text-xl font-bold text-cream tracking-wide font-headline leading-tight">SCOREIA</h1>
                <div class="text-[9px] font-medium text-cream/50 uppercase tracking-widest">Riesgo Crediticio</div>
            </div>
        </a>"""

for fname in files:
    filepath = os.path.join(base_dir, fname)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        if old_nav_logo in content:
            content = content.replace(old_nav_logo, new_nav_logo)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

# 2. Update login.html Left Panel Logo
login_path = os.path.join(base_dir, 'login.html')
if os.path.exists(login_path):
    with open(login_path, 'r', encoding='utf-8') as f:
        login_content = f.read()

    old_login_left = """            <a href="/" class="inline-block hover:scale-105 transition-transform">
                <div class="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-surface border border-cream/10 mb-6 shadow-[0_0_30px_rgba(57,138,72,0.3)]">
                    <span class="material-symbols-outlined text-4xl text-accent">blur_on</span>
                </div>
            </a>"""

    new_login_left = """            <a href="/" class="inline-flex items-center gap-4 hover:scale-105 transition-transform mb-8 group">
                <div class="w-14 h-14 rounded-2xl bg-surface flex items-center justify-center border border-cream/10 shadow-[0_0_25px_rgba(57,138,72,0.3)] group-hover:shadow-[0_0_35px_rgba(57,138,72,0.5)] transition-shadow">
                    <span class="material-symbols-outlined text-3xl text-accent font-bold">blur_on</span>
                </div>
                <div class="flex flex-col justify-center">
                    <h1 class="text-2xl font-bold text-cream tracking-wide font-headline leading-tight">SCOREIA</h1>
                    <div class="text-[10px] font-medium text-cream/50 uppercase tracking-widest">Riesgo Crediticio</div>
                </div>
            </a>"""

    if old_login_left in login_content:
        login_content = login_content.replace(old_login_left, new_login_left)

    old_login_mobile = """            <div class="text-center mb-8 lg:hidden">
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-xl bg-surface flex items-center justify-center border border-cream/10 shadow-[0_0_15px_rgba(57,138,72,0.2)]">
                        <span class="material-symbols-outlined text-accent text-3xl">blur_on</span>
                    </div>
                    <h1 class="text-3xl font-bold text-cream tracking-wide font-headline">SCOREIA</h1>
                </div>
            </div>"""

    new_login_mobile = """            <div class="text-center mb-8 lg:hidden">
                <div class="flex items-center justify-center gap-3">
                    <div class="w-10 h-10 rounded-xl bg-surface flex items-center justify-center border border-cream/10 shadow-[0_0_15px_rgba(57,138,72,0.2)]">
                        <span class="material-symbols-outlined text-accent text-3xl">blur_on</span>
                    </div>
                    <div class="flex flex-col text-left">
                        <h1 class="text-2xl font-bold text-cream tracking-wide font-headline leading-tight">SCOREIA</h1>
                        <div class="text-[9px] font-medium text-cream/50 uppercase tracking-widest">Riesgo Crediticio</div>
                    </div>
                </div>
            </div>"""

    if old_login_mobile in login_content:
        login_content = login_content.replace(old_login_mobile, new_login_mobile)
        
    with open(login_path, 'w', encoding='utf-8') as f:
        f.write(login_content)

print("Updated branding across files.")
