import requests
import random
import time

API_URL = "http://localhost:8000"

MATERIALS = [
    {"type": "PP-H", "form": "Granül", "color": "Natürel", "loc": "Gebze / Kocaeli"},
    {"type": "LDPE", "form": "Orijinal Granül", "color": "Şeffaf", "loc": "Aliağa / İzmir"},
    {"type": "HDPE", "form": "Orijinal Granül", "color": "Beyaz", "loc": "Çerkezköy / Tekirdağ"},
    {"type": "rPET", "form": "Çapak (Flake)", "color": "Karışık Renkli", "loc": "Gaziantep"},
    {"type": "ABS", "form": "Granül", "color": "Siyah", "loc": "Tuzla / İstanbul"},
    {"type": "PA6", "form": "Granül", "color": "Natürel", "loc": "Manisa"},
    {"type": "EVA", "form": "Granül", "color": "Şeffaf", "loc": "Çorlu / Tekirdağ"},
    {"type": "PVC-S", "form": "Toz", "color": "Beyaz", "loc": "Adana"},
    {"type": "MB-WHT", "form": "Granül", "color": "Beyaz", "loc": "Bursa"},
    {"type": "MB-BLK", "form": "Granül", "color": "Siyah", "loc": "Kayseri"},
    {"type": "TPU", "form": "Granül", "color": "Şeffaf", "loc": "İstanbul Avrupa"},
    {"type": "LLDPE", "form": "Orijinal", "color": "Şeffaf", "loc": "İzmir Serbest Bölge"},
]

CRITERIA_IDS = [
    "mfi_dev", "nem", "gorsel", "koku", "seffaflik", "yog_dev", 
    "renk_tut", "fiziksel", "kirilma", "cekme", "dsc", "ambalaj", 
    "mensei", "parti_sureklilik", "cevre", "yuzey_parlaklik"
]

def generate_random_criteria():
    return {c: random.randint(70, 100) for c in CRITERIA_IDS}

def seed_products():
    print("Starting seeding of 50 products...")
    for i in range(50):
        mat = random.choice(MATERIALS)
        mfi = round(random.uniform(0.5, 45.0), 2)
        density = round(random.uniform(0.85, 1.4), 3)
        qty = round(random.uniform(5.0, 150.0), 1)
        
        # 1. Teklif Oluştur
        offer_payload = {
            "material_type": mat["type"],
            "material_form": mat["form"],
            "color": mat["color"],
            "location": mat["loc"],
            "declared_mfi": mfi,
            "declared_density": density,
            "quantity_tons": qty
        }
        
        try:
            res = requests.post(f"{API_URL}/offers/", json=offer_payload)
            if res.status_code == 200:
                offer_id = res.json()["id"]
                
                # 2. Exper Onayı ile Piyasaya Sür (Guaranteed Lot yap)
                scores = generate_random_criteria()
                # Rasgele bazılarını "kusursuz" yapalım
                if random.random() > 0.7:
                    scores = {c: random.randint(95, 100) for c in CRITERIA_IDS} # A+
                    
                approve_payload = {"criteria_scores": scores}
                app_res = requests.post(f"{API_URL}/admin/approve_offer/{offer_id}", json=approve_payload)
                
                if app_res.status_code == 200:
                    lot = app_res.json()
                    print(f"[{i+1}/50] Created Lot: {lot['material_type']} - Score: {lot.get('carbon_score', '?')}")
                else:
                    print(f"Failed to approve offer {offer_id}: {app_res.text}")
            else:
                print(f"Failed to create offer: {res.text}")
        except Exception as e:
            print(f"Error on iteration {i}: {e}")
            
    print("Data seeding completed!")

if __name__ == "__main__":
    seed_products()
