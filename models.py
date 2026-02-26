import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    role = Column(String, default="user") # user (buyer/seller same), admin
    hashed_password = Column(String)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    
    offers = relationship("Offer", back_populates="seller")

class Offer(Base):
    """
    Satıcının 'Elimde mal var, trink satmak istiyorum' dediği teklif tabiri.
    """
    __tablename__ = "offers"

    id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer, ForeignKey("users.id"))
    material_type = Column(String) # PP, PE, PVC
    material_form = Column(String, default="Granül")
    declared_mfi = Column(Float)
    declared_density = Column(Float)
    quantity_tons = Column(Float)
    
    # EcoGrade Exper Workflow
    status = Column(String, default="Pending") # Pending, AwaitingSample, Approved, Rejected
    ai_estimated_price_usd = Column(Float, nullable=True)
    lab_mfi = Column(Float, nullable=True)
    lab_density = Column(Float, nullable=True)
    
    custom_fields = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    seller = relationship("User", back_populates="offers")
    guaranteed_lots = relationship("GuaranteedLot", back_populates="original_offer")

class GuaranteedLot(Base):
    """
    EcoGrade Exper testinden geçip platform havuzuna alınan (satışa hazır) garantili parti.
    """
    __tablename__ = "guaranteed_lots"

    id = Column(Integer, primary_key=True, index=True)
    original_offer_id = Column(Integer, ForeignKey("offers.id"))
    material_type = Column(String)
    material_form = Column(String, default="Granül")
    mfi = Column(Float) # Exper (Lab) onaylı kesin MFI
    density = Column(Float) # Exper onaylı kesin yoğunluk
    quantity_tons = Column(Float)
    
    # Platform Satış Fiyatı (EcoGrade Kar Marjı Eklenmiş Hal)
    selling_price_usd = Column(Float)
    carbon_score = Column(String) # A+, B
    quality_score_numeric = Column(Float, nullable=True) # 0-100 arası ağırlıklı puan
    is_active = Column(Boolean, default=True)
    
    custom_fields = Column(JSON, default=dict)
    
    original_offer = relationship("Offer", back_populates="guaranteed_lots")
    
    @property
    def seller_name(self):
        if self.original_offer and self.original_offer.seller:
            return self.original_offer.seller.company_name
        return "EcoGrade A.Ş."

class PurchaseRequest(Base):
    """
    Alıcının 'Bana bu özelliklerde mal lazım' dediği talep (Tersine pazar yeri).
    """
    __tablename__ = "requests"

    id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(Integer, ForeignKey("users.id"))
    material_type = Column(String)
    min_mfi = Column(Float)
    max_mfi = Column(Float)
    min_density = Column(Float)
    max_density = Column(Float)
    target_quantity_tons = Column(Float)
    
    status = Column(String, default="Open") # Open, Fulfilled

class Order(Base):
    """
    Alıcının lot üzerinden satın alıp ESCROW havuzuna para yatırdığı işlemler.
    """
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(Integer, ForeignKey("users.id"))
    lot_id = Column(Integer, ForeignKey("guaranteed_lots.id"))
    quantity_tons = Column(Float)
    total_amount_usd = Column(Float)
    
    incoterms = Column(String, default="EXW") # EXW, FOB, CIF
    payment_status = Column(String, default="Escrow_Pending") # Escrow_Pending, Escrow_Funded, Released_to_Seller, Refunded
    
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

class Conversation(Base):
    """Alıcı-Satıcı arasındaki mesajlaşma odası."""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    lot_id = Column(Integer, ForeignKey("guaranteed_lots.id"), nullable=True)
    buyer_id = Column(Integer, ForeignKey("users.id"))
    seller_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    
    messages = relationship("Message", back_populates="conversation")

class Message(Base):
    """Konuşma içindeki tekil mesaj."""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    sender_id = Column(Integer, ForeignKey("users.id"))
    text = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    
    conversation = relationship("Conversation", back_populates="messages")
