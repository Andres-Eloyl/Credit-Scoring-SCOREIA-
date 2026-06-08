import os

filepath = r'app\ui\app.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

spinners_css = """
        /* Remove arrows from number inputs */
        input[type="number"]::-webkit-inner-spin-button,
        input[type="number"]::-webkit-outer-spin-button {
            -webkit-appearance: none;
            margin: 0;
        }
        input[type="number"] {
            -moz-appearance: textfield;
        }
"""

if "::-webkit-inner-spin-button" not in content:
    # Insert it right after .premium-input styles
    target = "color: #f5f5dc;\n        }"
    new_content = target + "\n" + spinners_css
    
    content = content.replace(target, new_content, 1)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Added CSS to hide number spinners in app.html")
else:
    print("Spinners CSS already exists")
