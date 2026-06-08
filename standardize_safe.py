import os
import re
import glob

html_files = glob.glob('app/ui/*.html')

google_fonts_link = '<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Space+Grotesk:wght@300;400;500;600;700&display=swap" rel="stylesheet"/>'

for filepath in html_files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Standardize Google Fonts link
    content = re.sub(r'<link href="https://fonts\.googleapis\.com/css2\?family=[^>]+>\s*', '', content)
    content = content.replace('</head>', f'    {google_fonts_link}\n</head>')

    # 2. Tailwind Config
    font_family_config = """fontFamily: {
                "headline": ["Space Grotesk", "sans-serif"],
                "body": ["Outfit", "sans-serif"]
            }"""
    if 'fontFamily:' in content:
        content = re.sub(r'fontFamily:\s*\{[^}]*\}', font_family_config, content, flags=re.DOTALL)
    else:
        content = re.sub(r'extend:\s*\{', 'extend: {\n            ' + font_family_config + ',', content)

    # 3. Standardize Body tag
    content = re.sub(r'(<body[^>]+class="[^"]*)font-body[^\s"]*', r'\1', content)
    content = re.sub(r'(<body[^>]+class="[^"]*)(")', r'\1 font-body\2', content)

    # 4. Remove heavy weights
    content = content.replace('font-extrabold', 'font-bold')
    content = content.replace('font-black', 'font-bold')

    # 5. Add font-headline cleanly
    def clean_and_add_headline(match):
        full_match = match.group(0)
        cls_str = match.group(1)
        # remove existing font-headline* or font-display*
        cls_str = re.sub(r'\s*font-headline(?:-[a-z]+)?', '', cls_str)
        cls_str = re.sub(r'\s*font-display(?:-[a-z]+)?', '', cls_str)
        # inject back
        return full_match.replace(match.group(1), f'{cls_str} font-headline')

    content = re.sub(r'class="([^"]*text-(?:2xl|3xl|4xl|5xl|6xl|7xl)[^"]*)"', clean_and_add_headline, content)
    
    def h_headline(m):
        full_match = m.group(0)
        if 'font-headline' not in full_match:
            return re.sub(r'class="([^"]*)"', r'class="\1 font-headline"', full_match)
        return full_match

    content = re.sub(r'<h[123][^>]+class="[^"]*"', h_headline, content)

    # 6. Clean up multiple spaces
    content = re.sub(r'class="([^"]*)"', lambda m: 'class="' + re.sub(r'\s+', ' ', m.group(1)).strip() + '"', content)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

print("Done")
