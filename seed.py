import sys
import os

# Set up to ensure models and database are available
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, engine, Base
from models import GuaranteedLot

# Ensure tables exist
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# clear existing lots first
db.query(GuaranteedLot).delete()

lots = [
    GuaranteedLot(material_type="PP-H (Polipropilen)", mfi=12.5, density=0.905, quantity_tons=24.5, selling_price_usd=1240.0, carbon_score="B", is_active=True),
    GuaranteedLot(material_type="LDPE (Polietilen)", mfi=2.1, density=0.920, quantity_tons=15.0, selling_price_usd=980.0, carbon_score="A", is_active=True),
    GuaranteedLot(material_type="ABS", mfi=18.0, density=1.04, quantity_tons=5.0, selling_price_usd=1340.0, carbon_score="B", is_active=True),
    GuaranteedLot(material_type="Recycle PET Flake", mfi=32.0, density=1.38, quantity_tons=100.0, selling_price_usd=720.0, carbon_score="A+", is_active=True),
    GuaranteedLot(material_type="Off-Grade PVC K67", mfi=0, density=1.40, quantity_tons=40.0, selling_price_usd=895.0, carbon_score="B+", is_active=True),
    GuaranteedLot(material_type="PA6 (Nylon)", mfi=14.0, density=1.14, quantity_tons=12.0, selling_price_usd=2100.0, carbon_score="C", is_active=True),
    GuaranteedLot(material_type="Off-Grade HDPE", mfi=0.8, density=0.960, quantity_tons=65.5, selling_price_usd=1080.0, carbon_score="B+", is_active=True),
    GuaranteedLot(material_type="Recycle PP-C", mfi=8.0, density=0.90, quantity_tons=200.0, selling_price_usd=950.0, carbon_score="A+", is_active=True),
    GuaranteedLot(material_type="EPS Regular", mfi=0, density=1.05, quantity_tons=18.5, selling_price_usd=1450.0, carbon_score="C", is_active=True),
    GuaranteedLot(material_type="PC (Polikarbonat)", mfi=10.0, density=1.20, quantity_tons=8.0, selling_price_usd=2800.0, carbon_score="B", is_active=True),
]

for lot in lots:
    db.add(lot)
db.commit()
db.close()
print("Sistem basariyla 10 adet gercek-sakinimli test lot'u ile beslendi.")
