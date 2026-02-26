from database import SessionLocal
from models import Offer
from datetime import datetime

db = SessionLocal()

# Add 2 sample offers
offer1 = Offer(
    seller_id=1,
    material_type="PP",
    material_form="Granül",
    declared_mfi=12.5,
    declared_density=0.91,
    quantity_tons=24.5,
    status="AwaitingSample",
    ai_estimated_price_usd=1200.0,
    created_at=datetime.utcnow()
)

offer2 = Offer(
    seller_id=1,
    material_type="HDPE",
    material_form="Çapak",
    declared_mfi=2.1,
    declared_density=0.95,
    quantity_tons=55.0,
    status="AwaitingSample",
    ai_estimated_price_usd=1150.0,
    created_at=datetime.utcnow()
)

db.add(offer1)
db.add(offer2)
db.commit()

print("Successfully added 2 example offers to the database directly via SQLAlchemy.")
db.close()
