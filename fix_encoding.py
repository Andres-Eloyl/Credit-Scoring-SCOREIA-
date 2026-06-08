import os

files = ['index.html', 'about.html', 'features.html', 'support.html', 'tech.html', 'theory.html', 'use_cases.html']
base_dir = r'app\ui'

for fname in files:
    filepath = os.path.join(base_dir, fname)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Fix encoding glitches in nav
    content = content.replace('TecnologA-a', 'Tecnología')
    content = content.replace('TecnologÃ\xada', 'Tecnología')
    content = content.replace('AndrÃ©s Eloy LÃ³pez', 'Andrés Eloy López')
    content = content.replace('AndrAcs Eloy LA3pez', 'Andrés Eloy López')
    content = content.replace('DiseA\x1fando', 'Diseñando')
    content = content.replace('DiseA\x1aando', 'Diseñando')
    content = content.replace('aprobaciA3n', 'aprobación')
    content = content.replace('crAcdito', 'crédito')
    content = content.replace('prAcstamos', 'préstamos')
    content = content.replace('drA\xa0sticamente', 'drásticamente')
    content = content.replace('comitAc', 'comité')
    content = content.replace('evaluaciA3n', 'evaluación')
    content = content.replace('colocaciA3n', 'colocación')
    content = content.replace('fricciA3n', 'fricción')
    content = content.replace('predicciA3n', 'predicción')
    content = content.replace('clA\xa0sicos', 'clásicos')
    content = content.replace('Tecnologa', 'Tecnología')
    content = content.replace('Andrs Eloy Lpez', 'Andrés Eloy López')
    content = content.replace('Diseando', 'Diseñando')
    
    # Standardize the header wrappers
    # In features, tech, theory, use_cases, support:
    content = content.replace('<div class="text-center mb-16">', '<div class="max-w-4xl mx-auto text-center mb-16">')
    # In about:
    content = content.replace('<div class="max-w-3xl mx-auto text-center">', '<div class="max-w-4xl mx-auto text-center mb-16">')
    # In index:
    content = content.replace('<div class="max-w-4xl mx-auto text-center">', '<div class="max-w-4xl mx-auto text-center mb-16">')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'Fixed {fname}')
