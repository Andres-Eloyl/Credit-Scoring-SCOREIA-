import requests

try:
    resp = requests.get('https://countriesnow.space/api/v0.1/countries/positions', timeout=5)
    print("Countries:", resp.json()['data'][0:2])
    
    resp2 = requests.post('https://countriesnow.space/api/v0.1/countries/states', json={'country': 'Venezuela'}, timeout=5)
    print("States:", resp2.json()['data']['states'][0:2])
    
    resp3 = requests.post('https://countriesnow.space/api/v0.1/countries/state/cities', json={'country': 'Venezuela', 'state': 'Miranda'}, timeout=5)
    print("Cities:", resp3.json()['data'][0:2])
except Exception as e:
    print("Error:", e)
