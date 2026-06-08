import os

filepath = r'app\ui\app.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old_input = '<input class="premium-input" type="text" id="client_id" name="client_id" autocomplete="off" required/>'
new_input = '<input class="premium-input" type="text" id="client_id" name="client_id" autocomplete="new-password" maxlength="8" placeholder="Ej: 12345678" oninput="this.value = this.value.replace(/[^0-9]/g, \'\')" required/>'

if old_input in content:
    content = content.replace(old_input, new_input)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed Cedula input!")
else:
    print("Could not find the target input line.")
