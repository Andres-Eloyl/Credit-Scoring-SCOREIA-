import glob

for f in glob.glob('app/ui/*.html'):
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
        print(f"--- {f} ---")
        print(content[:600])
        print("\n\n")
