import os

files_to_edit = ['index.html', 'about.html', 'features.html', 'support.html', 'tech.html', 'theory.html', 'use_cases.html']
base_dir = r'app\ui'

for fname in files_to_edit:
    filepath = os.path.join(base_dir, fname)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if fname == 'index.html':
        content = content.replace('<section class="min-h-screen flex items-center justify-center pt-20 px-6">', '<section class="px-6 animate-hero pt-12">')
        content = content.replace('<div class="max-w-4xl mx-auto text-center mt-24">', '<div class="max-w-4xl mx-auto text-center">')
    else:
        content = content.replace('<section class="px-6 animate-hero">', '<section class="px-6 animate-hero pt-12">')
        
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'Standardized section in {fname}')
