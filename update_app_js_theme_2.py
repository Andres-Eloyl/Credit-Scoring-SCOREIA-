import os

filepath = r'app\ui\app.js'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# We will just find the index of "function hexToRgb(hex)" and the index of "function syncConfigUI()"
start_idx = content.find("function hexToRgb(hex)")
end_idx = content.find("function syncConfigUI()")

if start_idx != -1 and end_idx != -1:
    old_block = content[start_idx:end_idx]
    
    new_block = """function hexToRgb(hex) {
        var result = /^#?([a-f\\d]{2})([a-f\\d]{2})([a-f\\d]{2})$/i.exec(hex);
        if(!result) return { space: '57 138 72', comma: '57, 138, 72' };
        return {
            space: parseInt(result[1], 16) + ' ' + parseInt(result[2], 16) + ' ' + parseInt(result[3], 16),
            comma: parseInt(result[1], 16) + ', ' + parseInt(result[2], 16) + ', ' + parseInt(result[3], 16)
        };
    }

    function applyThemeConfig() {
        if (currentConfig.theme === 'dark') {
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
        }

        const c = currentConfig.accentColor;
        const rgbVals = hexToRgb(c);
        
        document.documentElement.style.setProperty('--color-accent', rgbVals.space);
        document.documentElement.style.setProperty('--color-accent-comma', rgbVals.comma);
        
        let styleTag = document.getElementById('dynamic-accent-style');
        if (styleTag) {
            styleTag.remove();
        }
    }
    
    """
    
    content = content.replace(old_block, new_block)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Updated app.js theme logic!")
else:
    print("Could not find the blocks.")
