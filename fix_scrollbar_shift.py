import glob

html_files = glob.glob('app/ui/*.html')

for filepath in html_files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Enforce overflow-y-scroll to prevent layout shifting
    content = content.replace('overflow-x-hidden', 'overflow-y-scroll overflow-x-hidden')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

print("overflow-y-scroll added")
