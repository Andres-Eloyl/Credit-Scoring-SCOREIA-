import os

filepath = r'app\ui\app.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old_input = '<input class="premium-input" type="text" id="client_id" name="client_id" autocomplete="new-password" maxlength="8" placeholder="Ej: 12345678" oninput="this.value = this.value.replace(/[^0-9]/g, \'\')" required/>'

# We remove maxlength="8" so the browser can paste "c-12345678" fully before JS processes it.
# Then JS removes letters, and forces the length to 8 max.
new_input = '<input class="premium-input" type="text" id="client_id" name="client_id" autocomplete="new-password" placeholder="Ej: 12345678" oninput="let v = this.value.replace(/[^0-9]/g, \'\'); this.value = v.slice(0, 8);" onchange="let v = this.value.replace(/[^0-9]/g, \'\'); this.value = v.slice(0, 8);" required/>'

if old_input in content:
    content = content.replace(old_input, new_input)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed Cedula input autocomplete issue!")
else:
    print("Could not find the target input line.")
