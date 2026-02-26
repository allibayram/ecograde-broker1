import pandas as pd
from sqlalchemy.orm import Session
import random
import os

from database import engine, SessionLocal
import models
import schemas

def seed_db():
    print("Veritabanı tabloları oluşturuluyor...")
    models.Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    # Clean existing lots
    db.query(models.GuaranteedLot).delete()
    db.commit()
    
    print("Kitap.xlsx okunuyor...")
    excel_path = r"c:\Users\Ali Furkan\Desktop\ilhan dayım\proje genel hatlar\Kitap.xlsx"
    df = pd.read_excel(excel_path)
    
    # Clean DataFrame
    df = df.dropna(subset=["Malzeme Adı"])
    print(f"Toplam {len(df)} ürün bulundu.")
    
    categories = ["ECOGRADE PRIME", "ECOGRADE OFF", "ECOGRADE COMP", "ECOGRADE RECYCLE"]
    scores = ["A+", "A", "B", "C"]
    
    mock_lots = []
    
    for index, row in df.iterrows():
        malzeme_adi = str(row["Malzeme Adı"]).strip()
        kod = str(row["Kod"]).strip() if pd.notna(row["Kod"]) else "N/A"
        
        # MFI ve Density için rastgele ama gerçekçi değerler
        mfi = round(random.uniform(2.0, 50.0), 2)
        density = round(random.uniform(0.85, 1.25), 3)
        qty = round(random.uniform(10.0, 500.0), 1)
        price = round(random.uniform(900.0, 2500.0), 2)
        
        lot = models.GuaranteedLot(
            material_type=malzeme_adi,
            mfi=mfi,
            density=density,
            quantity_tons=qty,
            selling_price_usd=price,
            carbon_score=random.choice(scores),
            is_active=True,
            original_offer_id=None
        )
        mock_lots.append(lot)
        
        # Sadece ilk 50 ürün yeterli (demo amaçlı çok fazla kasmamak için)
        if len(mock_lots) >= 50:
            break
            
    db.add_all(mock_lots)
    db.commit()
    
    print(f"Başarıyla {len(mock_lots)} adet gerçek ürün sisteme (DB) işlendi.")
    
    # Frontend filtreleri için unique polimer tipleri çıkaralım
    types = list(df["Malzeme Adı"].dropna().unique())
    print("\nBenzersiz Polimer Tipleri:")
    print(types[:10])
    
    db.close()

if __name__ == "__main__":
    seed_db()
