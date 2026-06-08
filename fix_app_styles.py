import os

filepath = r'app\ui\app.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

styles_to_add = """
        .glass-panel-premium {
            background: linear-gradient(145deg, rgba(20,28,22,0.6) 0%, rgba(10,14,10,0.8) 100%);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(245, 245, 220, 0.05);
            box-shadow: 0 20px 40px rgba(0,0,0,0.4);
        }

        /* --- Premium Input Styles --- */
        .premium-input-container {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }
        .premium-label {
            font-size: 0.75rem; 
            font-weight: 700; 
            color: rgba(245, 245, 220, 0.6); 
            text-transform: uppercase;
            letter-spacing: 0.1em; 
            font-family: "Outfit", sans-serif;
        }
        .premium-input {
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
        }
        .premium-input:focus {
            border-color: rgba(57, 138, 72, 0.5) !important; 
            box-shadow: 0 0 15px rgba(57, 138, 72, 0.2) !important;
            outline: none !important;
            ring: 0 !important;
        }
        .premium-input::placeholder {
            color: rgba(245, 245, 220, 0.3) !important;
        }
        select.premium-input option {
            background-color: #101410; 
            color: #f5f5dc;
        }
"""

if "Premium Input Styles" not in content:
    # Replace the existing glass-panel-premium with the updated block
    content = content.replace("""        .glass-panel-premium {
            background: linear-gradient(145deg, rgba(20,28,22,0.6) 0%, rgba(10,14,10,0.8) 100%);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(245, 245, 220, 0.05);
            box-shadow: 0 20px 40px rgba(0,0,0,0.4);
        }""", styles_to_add)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Added premium-input styles to app.html")
else:
    print("Styles already present")
