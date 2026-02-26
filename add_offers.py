import urllib.request
import json

offers = [
    {
        "material_type": "PP",
        "material_form": "Granül",
        "declared_mfi": 12.5,
        "declared_density": 0.91,
        "quantity_tons": 24.5
    },
    {
        "material_type": "HDPE",
        "material_form": "Çapak",
        "declared_mfi": 2.1,
        "declared_density": 0.95,
        "quantity_tons": 55.0
    }
]

for offer in offers:
    data = json.dumps(offer).encode('utf-8')
    req = urllib.request.Request('http://127.0.0.1:8000/offers/', data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as res:
            print("Success:", res.read().decode())
    except Exception as e:
        print("Error:", e)
