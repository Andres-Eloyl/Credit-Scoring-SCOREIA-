import os
import glob

base_dir = r'app\ui'
html_files = glob.glob(os.path.join(base_dir, '*.html'))

old_tw = """    <script id="tailwind-config">
      tailwind.config = {
        darkMode: "class",
        theme: {
          extend: {
            colors: {
                "accent": "#398a48","""

new_tw = """    <script>
      function initAccent() {
        var h = localStorage.getItem('accentColor') || '#398a48';
        var r = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(h);
        if(r) {
          var rgbSpc = parseInt(r[1], 16) + ' ' + parseInt(r[2], 16) + ' ' + parseInt(r[3], 16);
          var rgbCom = parseInt(r[1], 16) + ', ' + parseInt(r[2], 16) + ', ' + parseInt(r[3], 16);
          document.documentElement.style.setProperty('--color-accent', rgbSpc);
          document.documentElement.style.setProperty('--color-accent-comma', rgbCom);
        }
      }
      initAccent();
    </script>
    <script id="tailwind-config">
      tailwind.config = {
        darkMode: "class",
        theme: {
          extend: {
            colors: {
                "accent": "rgb(var(--color-accent) / <alpha-value>)", """

for filepath in html_files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    modified = False
    
    if old_tw in content:
        content = content.replace(old_tw, new_tw)
        modified = True
    
    # Replace the hardcoded rgb values in CSS
    if "rgba(57, 138, 72," in content:
        content = content.replace("rgba(57, 138, 72,", "rgba(var(--color-accent-comma),")
        modified = True

    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {os.path.basename(filepath)}")

print("HTML files updated.")
