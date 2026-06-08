import os

filepath = r'app\ui\login.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove bold tags from the added text
content = content.replace("<strong>trazabilidad y seguridad bancaria</strong>", "trazabilidad y seguridad bancaria")

# 2. Fix the invalid font-body-md class to font-body so the Outfit font actually applies to all inputs
content = content.replace("font-body-md", "font-body text-sm")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed fonts and removed bold text in login.html")
