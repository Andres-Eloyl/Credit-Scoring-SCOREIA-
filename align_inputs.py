import os
import re

filepath = r'app\ui\app.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update the CSS for identical sizes
old_css = """        .premium-input {
            width: 100%;
            background-color: rgba(0, 0, 0, 0.4) !important; 
            border: 1px solid rgba(245, 245, 220, 0.1) !important; 
            border-radius: 0.75rem; 
            padding: 0.875rem 1rem; 
            color: #f5f5dc !important; 
            font-family: "Outfit", sans-serif;
            font-size: 0.875rem; 
            transition: all 0.3s ease;
            outline: none;
            box-shadow: none !important;
        }"""

new_css = """        .premium-input {
            width: 100%;
            height: 48px !important;
            box-sizing: border-box !important;
            background-color: rgba(0, 0, 0, 0.4) !important; 
            border: 1px solid rgba(245, 245, 220, 0.1) !important; 
            border-radius: 0.75rem !important; 
            padding: 0 1rem !important; 
            color: #f5f5dc !important; 
            font-family: "Outfit", sans-serif;
            font-size: 0.875rem; 
            transition: all 0.3s ease;
            outline: none;
            box-shadow: none !important;
            line-height: normal;
        }"""

content = content.replace(old_css, new_css)

# 2. Add autocomplete="off" to Cedula
old_input = '<input class="premium-input" type="text" id="client_id" name="client_id" required/>'
new_input = '<input class="premium-input" type="text" id="client_id" name="client_id" autocomplete="off" required/>'
content = content.replace(old_input, new_input)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated app.html with perfect input sizes and removed autocomplete.")
