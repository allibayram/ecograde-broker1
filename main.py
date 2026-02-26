from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from fastapi.middleware.cors import CORSMiddleware
import models, schemas
from database import engine, get_db, init_db
from auth import get_password_hash, verify_password, create_access_token, get_current_user, require_auth
import datetime
import traceback

# Create database tables (with error handling for serverless)
init_db()

app = FastAPI(
    title="EcoGrade Broker API", 
    description="Managed Marketplace (Kavak/Arabam.com Modeli) B2B API", 
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "https://broker-frontend-nu.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "EcoGrade Broker Core Engine v2 is running."}

@app.get("/debug/db")
def debug_db():
    """Debug endpoint to test database connection"""
    import os
    engine_url = str(engine.url)
    # Mask password
    if "@" in engine_url:
        parts = engine_url.split("@")
        user_part = parts[0].rsplit(":", 1)
        engine_url = user_part[0] + ":****@" + parts[1]
    
    try:
        from sqlalchemy import text
        db = next(get_db())
        result = db.execute(text("SELECT 1"))
        db.close()
        return {
            "status": "OK",
            "engine_url": engine_url,
            "vercel_env": os.environ.get("VERCEL", "NOT SET"),
            "connection": "SUCCESS",
            "tables_created": init_db()
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "engine_url": engine_url,
            "vercel_env": os.environ.get("VERCEL", "NOT SET"),
            "error": str(e),
            "error_type": type(e).__name__
        }

# --- AUTH ENDPOINTS ---
@app.post("/auth/register")
def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    """Yeni kullanıcı kaydı"""
    existing = db.query(models.User).filter(models.User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Bu e-posta adresi zaten kayıtlı")
    
    hashed = get_password_hash(user_data.password)
    db_user = models.User(
        company_name=user_data.company_name,
        email=user_data.email,
        role=user_data.role or "user",
        hashed_password=hashed,
        is_verified=False
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    token = create_access_token(data={"sub": db_user.email})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": db_user.id,
            "email": db_user.email,
            "company_name": db_user.company_name,
            "role": db_user.role,
            "is_verified": db_user.is_verified
        }
    }

@app.post("/auth/login")
def login_user(credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    """Kullanıcı girişi — JWT token döndürür"""
    user = db.query(models.User).filter(models.User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Geçersiz e-posta veya şifre")
    
    token = create_access_token(data={"sub": user.email})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "company_name": user.company_name,
            "role": user.role,
            "is_verified": user.is_verified
        }
    }

@app.get("/auth/me")
def get_me(current_user: models.User = Depends(require_auth)):
    """Mevcut kullanıcı bilgilerini döndürür"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "company_name": current_user.company_name,
        "role": current_user.role,
        "is_verified": current_user.is_verified
    }

# --- BROKER LOGIC (TRINK SAT - SELLER FLOW) ---
def estimate_price(material_type: str, mfi: float, density: float) -> float:
    # AI tabanlı fiyat tahmini - MFI ve yoğunluk faktörleniyor
    base_price = {
        "PP": 1200, "PP-H": 1250, "PP-C": 1220, "PP-R": 1230,
        "PE": 1100, "LDPE": 1080, "LLDPE": 1120, "HDPE": 1150, "MDPE": 1100,
        "PVC": 900, "PVC-S": 920, "PVC-P": 880,
        "ABS": 1500, "SAN": 1350, "ASA": 1400,
        "PET": 1050, "PBT": 1600, "PC": 2200, "PC-ABS": 1900,
        "POM": 1700, "PA6": 1800, "PA66": 2100,
        "PS-GP": 1000, "PS-HI": 1050, "PMMA": 2000,
        "rPP": 800, "rHDPE": 750, "rPET": 700,
        "TPU": 2500, "TPE-S": 1800, "POE": 1600, "EPDM": 1900,
        "EVA": 1300,
        "MB-WHT": 1400, "MB-BLK": 1200, "MB-COL": 1500,
        "CACO3": 600, "TALK": 700, "GF": 1800,
    }.get(material_type, 1000)
    
    # MFI etkisi: düşük MFI = daha sert = %3 prim, yüksek MFI = %2 indirim
    mfi_factor = 1.0
    if mfi < 5:
        mfi_factor = 1.03
    elif mfi > 20:
        mfi_factor = 0.98
    
    # Yoğunluk etkisi: yüksek yoğunluk = daha ağır = %2 prim
    density_factor = 1.0
    if density > 1.0:
        density_factor = 1.02
    elif density < 0.9:
        density_factor = 0.97
    
    # Rastgele varyasyon (%±3) ile fiyat çeşitliliği
    import random
    variation = random.uniform(0.97, 1.03)
    
    return round(base_price * mfi_factor * density_factor * variation, 2)

@app.post("/offers/", response_model=schemas.Offer)
def create_offer(offer: schemas.OfferCreate, db: Session = Depends(get_db), current_user: models.User = Depends(require_auth)):
    """ Satıcının elindeki malı EcoGrade'e satmak için form doldurması """
    import traceback
    try:
        estimated_price = estimate_price(offer.material_type, offer.declared_mfi, offer.declared_density)
        
        new_offer = models.Offer(
            **offer.model_dump(), 
            seller_id=current_user.id,
            ai_estimated_price_usd=estimated_price,
            status="AwaitingSample"
        )
        db.add(new_offer)
        db.commit()
        db.refresh(new_offer)
        return new_offer
    except Exception as e:
        with open("create_err.txt", "w") as f:
            f.write(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

# --- ADMIN / EXPER PANEL ENDPOINTS ---
@app.get("/admin/offers/", response_model=List[schemas.Offer])
def get_pending_offers(db: Session = Depends(get_db)):
    """ Exper'in test etmeyi beklediği numuneleri (ilanları) listeler """
    return db.query(models.Offer).filter(models.Offer.status == "AwaitingSample").all()

@app.post("/admin/approve_offer/{offer_id}", response_model=schemas.GuaranteedLot)
def approve_offer(offer_id: int, lab_data: schemas.AdminApproveOffer, db: Session = Depends(get_db)):
    """ Exper'in test sonucunu girip ilanı onaylayarak Pazaryerine (GuaranteedLot) düşürmesi """
    offer = db.query(models.Offer).filter(models.Offer.id == offer_id).first()
    if not offer:
        raise HTTPException(status_code=404, detail="İlan bulunamadı.")
    
    if offer.status != "AwaitingSample":
        raise HTTPException(status_code=400, detail="Bu ilan halihazırda onaylanmış veya reddedilmiş.")
        
    # Kriter Ağırlıkları (Toplam 53 Önem Puanı -> Maks 5300 skor)
    WEIGHTS = {
        "mfi": 5, "nem": 5, "katki": 5, "gorsel": 5, "koku": 5,
        "yogunluk": 3, "renk": 3, "fiziksel": 3, "kirilma": 3, "cekme": 3, "dsc": 3,
        "ambalaj": 2, "mensei": 2, "parti": 2, "cevre": 2, "yuzey": 2
    }
    
    # Gelen puanlar (100 üzerinden varsayılarak) ağırlıklı olarak hesaplanıyor
    total_weighted_score = 0
    max_possible_weighted = 5300 # Toplam Ağırlık 53 * 100
    
    for key, weight in WEIGHTS.items():
        score_val = lab_data.criteria_scores.get(key, 0)
        total_weighted_score += (score_val * weight)
        
    # 0-100 Formunda Quality Score
    final_quality_score = (total_weighted_score / max_possible_weighted) * 100 if max_possible_weighted > 0 else 0
    
    # Karbon / Kalite Skor A+, A, B, C hesaplama
    if final_quality_score >= 90:
        score_letter = "A+"
    elif final_quality_score >= 80:
        score_letter = "A"
    elif final_quality_score >= 60:
        score_letter = "B"
    else:
        score_letter = "C"
        
    # İlanı güncelle (Geçmiş versiyonla uyumlu alan güncellemeleri, veya null bırakılabilir)
    # offer'ın kendi içindeki lab_mfi, lab_density alanları eski yapıda kaldı o yüzden opsiyonellerse geçelim
    # Şimdilik enjekte edebileceğim lab_mfi ve lab_density null olarak kalabilir, ana olan criteria scores oldu.
    offer.status = "Approved"
    
    # Satış Havuzuna Orijinal olarak düşür
    selling_price = (offer.ai_estimated_price_usd or 1000.0) * 1.05 # EcoGrade broker marjı (%5)
    
    new_lot = models.GuaranteedLot(
        original_offer_id=offer.id,
        material_type=offer.material_type,
        mfi=offer.declared_mfi,  # Öncül MFI, artık esas puan skor oldu.
        density=offer.declared_density,
        quantity_tons=offer.quantity_tons,
        selling_price_usd=selling_price,
        carbon_score=score_letter,
        quality_score_numeric=final_quality_score,
        is_active=True
    )
    
    db.add(new_lot)
    db.commit()
    db.refresh(new_lot)
    return new_lot

# --- BROKER LOGIC (TALEP YARAT - BUYER FLOW) ---
@app.post("/requests/", response_model=schemas.PurchaseRequest)
def create_buyer_request(req: schemas.PurchaseRequestCreate, db: Session = Depends(get_db)):
    """ Alıcının listelerde kaybolmak yerine 'Bana şu maldan x Ton lazım' demesi """
    new_req = models.PurchaseRequest(
        **req.model_dump(),
        buyer_id=2 # Mock Buyer ID
    )
    db.add(new_req)
    db.commit()
    db.refresh(new_req)
    return new_req

@app.get("/guaranteed-lots/match", response_model=List[schemas.GuaranteedLot])
def match_guaranteed_lots(request_id: int, db: Session = Depends(get_db)):
    """ Alıcının talebine uygun olan ve bizzat EcoGrade Havuzunda bulunan onaylı malların getirilmesi """
    req = db.query(models.PurchaseRequest).filter(models.PurchaseRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Talep bulunamadı")
    
    matches = db.query(models.GuaranteedLot).filter(
        models.GuaranteedLot.is_active == True,
        models.GuaranteedLot.material_type == req.material_type,
        models.GuaranteedLot.mfi >= req.min_mfi,
        models.GuaranteedLot.mfi <= req.max_mfi,
        models.GuaranteedLot.density >= req.min_density,
        models.GuaranteedLot.density <= req.max_density
    ).all()
    
    return matches

# --- PRODUCTS (GUARANTEED LOTS) ENDPOINTS ---
@app.get("/products/")
def get_all_products(db: Session = Depends(get_db)):
    lots = db.query(models.GuaranteedLot).filter(models.GuaranteedLot.is_active == True).all()
    return [
        {
            "id": lot.id,
            "material_type": lot.material_type,
            "material_form": getattr(lot, 'material_form', None),
            "mfi": lot.mfi,
            "density": lot.density,
            "quantity_tons": lot.quantity_tons,
            "price_per_ton": lot.selling_price_usd,
            "selling_price_usd": lot.selling_price_usd,
            "carbon_score": lot.carbon_score,
            "is_active": lot.is_active,
            "original_offer_id": lot.original_offer_id,
            "created_at": getattr(lot, 'created_at', None),
            "manufacturer": "EcoGrade A.Ş.",
            "seller_name": lot.seller_name,
            "custom_fields": lot.custom_fields
        }
        for lot in lots
    ]

@app.put("/products/{product_id}")
def update_product(product_id: int, update_data: schemas.GuaranteedLotUpdate, db: Session = Depends(get_db)):
    lot = db.query(models.GuaranteedLot).filter(models.GuaranteedLot.id == product_id).first()
    if not lot:
        raise HTTPException(status_code=404, detail="Ürün bulunamadı")
    
    if update_data.selling_price_usd is not None:
        lot.selling_price_usd = update_data.selling_price_usd
    if update_data.is_active is not None:
        lot.is_active = update_data.is_active
    if update_data.custom_fields is not None:
        current = lot.custom_fields or {}
        new_fields = current.copy()
        new_fields.update(update_data.custom_fields)
        lot.custom_fields = new_fields
        
    db.commit()
    db.refresh(lot)
    return {"detail": f"Ürün #{product_id} başarıyla güncellendi", "custom_fields": lot.custom_fields, "seller_name": lot.seller_name}

@app.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    lot = db.query(models.GuaranteedLot).filter(models.GuaranteedLot.id == product_id).first()
    if not lot:
        raise HTTPException(status_code=404, detail="Ürün bulunamadı")
    lot.is_active = False
    db.commit()
    return {"detail": f"Ürün #{product_id} başarıyla gizlendi."}

@app.post("/products/match", response_model=List[schemas.GuaranteedLot])
def match_products_direct(req: schemas.PurchaseRequestCreate, db: Session = Depends(get_db)):
    # Veritabanına talep kaydetmeden eşleştirme listele (Market Hızlı Fitrelemesi için)
    query = db.query(models.GuaranteedLot).filter(models.GuaranteedLot.is_active == True)
    
    if req.material_type:
        query = query.filter(models.GuaranteedLot.material_type == req.material_type)
    if req.min_mfi:
        query = query.filter(models.GuaranteedLot.mfi >= req.min_mfi)
    if req.max_mfi:
        query = query.filter(models.GuaranteedLot.mfi <= req.max_mfi)
    if req.min_density:
        query = query.filter(models.GuaranteedLot.density >= req.min_density)
    if req.max_density:
        query = query.filter(models.GuaranteedLot.density <= req.max_density)
        
    return query.all()

# --- ESCROW CHECKOUT ---
@app.post("/checkout/", response_model=schemas.Order)
def checkout_lot(order_data: schemas.OrderCreate, db: Session = Depends(get_db)):
    """ Alıcının eşleşen lot için EcoGrade sistemine güvenli ödeme (Escrow) geçmesi """
    lot = db.query(models.GuaranteedLot).filter(models.GuaranteedLot.id == order_data.lot_id).first()
    if not lot:
        raise HTTPException(status_code=404, detail="Lot bulunamadı")
        
    if lot.quantity_tons < order_data.quantity_tons:
        raise HTTPException(status_code=400, detail="Yetersiz stok")
        
    total_usd = lot.selling_price_usd * order_data.quantity_tons
    
    new_order = models.Order(
        buyer_id=2, # Mock buyer
        lot_id=lot.id,
        quantity_tons=order_data.quantity_tons,
        total_amount_usd=total_usd,
        incoterms=order_data.incoterms,
        payment_status="Escrow_Funded" # Para havuza yattı
    )
    
    # Lot miktarını güncelle
    lot.quantity_tons -= order_data.quantity_tons
    if lot.quantity_tons <= 0:
        lot.is_active = False
        
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    return new_order

# --- MESSAGING ENDPOINTS ---
@app.post("/messages/")
def send_message(msg: schemas.MessageCreate, db: Session = Depends(get_db), current_user: models.User = Depends(require_auth)):
    """Mesaj gönder — konuşma yoksa otomatik oluşturur"""
    conv_id = msg.conversation_id
    
    if not conv_id:
        # Find or create conversation
        existing = db.query(models.Conversation).filter(
            ((models.Conversation.buyer_id == current_user.id) & (models.Conversation.seller_id == msg.receiver_id)) |
            ((models.Conversation.seller_id == current_user.id) & (models.Conversation.buyer_id == msg.receiver_id))
        ).first()
        
        if existing:
            conv_id = existing.id
        else:
            conv = models.Conversation(
                buyer_id=current_user.id,
                seller_id=msg.receiver_id,
                lot_id=msg.lot_id
            )
            db.add(conv)
            db.commit()
            db.refresh(conv)
            conv_id = conv.id
    
    new_msg = models.Message(
        conversation_id=conv_id,
        sender_id=current_user.id,
        text=msg.text
    )
    db.add(new_msg)
    db.commit()
    db.refresh(new_msg)
    
    return {
        "id": new_msg.id,
        "conversation_id": conv_id,
        "sender_id": new_msg.sender_id,
        "text": new_msg.text,
        "created_at": str(new_msg.created_at)
    }

@app.get("/messages/{conversation_id}")
def get_messages(conversation_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(require_auth)):
    """Bir konuşmadaki tüm mesajları getir"""
    conv = db.query(models.Conversation).filter(models.Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Konuşma bulunamadı")
    if conv.buyer_id != current_user.id and conv.seller_id != current_user.id:
        raise HTTPException(status_code=403, detail="Bu konuşmaya erişim yetkiniz yok")
    
    msgs = db.query(models.Message).filter(
        models.Message.conversation_id == conversation_id
    ).order_by(models.Message.created_at).all()
    
    return [
        {
            "id": m.id,
            "sender_id": m.sender_id,
            "text": m.text,
            "created_at": str(m.created_at),
            "is_me": m.sender_id == current_user.id
        }
        for m in msgs
    ]

@app.get("/messages/inbox/list")
def get_inbox(db: Session = Depends(get_db), current_user: models.User = Depends(require_auth)):
    """Kullanıcının tüm konuşmalarını getir"""
    convs = db.query(models.Conversation).filter(
        (models.Conversation.buyer_id == current_user.id) | 
        (models.Conversation.seller_id == current_user.id)
    ).all()
    
    result = []
    for conv in convs:
        last_msg = db.query(models.Message).filter(
            models.Message.conversation_id == conv.id
        ).order_by(models.Message.created_at.desc()).first()
        
        other_id = conv.seller_id if conv.buyer_id == current_user.id else conv.buyer_id
        other_user = db.query(models.User).filter(models.User.id == other_id).first()
        
        result.append({
            "id": conv.id,
            "lot_id": conv.lot_id,
            "buyer_id": conv.buyer_id,
            "seller_id": conv.seller_id,
            "created_at": str(conv.created_at),
            "last_message": last_msg.text if last_msg else None,
            "other_user_name": other_user.company_name if other_user else "Bilinmiyor"
        })
    
    return result
