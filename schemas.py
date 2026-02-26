from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# USER SCHEMAS
class UserBase(BaseModel):
    company_name: str
    email: str
    role: Optional[str] = "user"

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    company_name: str
    role: str
    is_verified: bool
    
    class Config:
        from_attributes = True

# OFFER (TRİNK SAT) SCHEMAS
class OfferBase(BaseModel):
    material_type: str
    material_form: str
    declared_mfi: float
    declared_density: float
    quantity_tons: float
    custom_fields: Optional[dict] = {}

class OfferCreate(OfferBase):
    pass

class Offer(OfferBase):
    id: int
    seller_id: int
    status: str
    ai_estimated_price_usd: Optional[float] = None
    lab_mfi: Optional[float] = None
    lab_density: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True

class AdminApproveOffer(BaseModel):
    criteria_scores: dict[str, int]  # 16 Kriterli test tablosu puanları (0-100 arası)

# GUARANTEED LOT SCHEMAS
class GuaranteedLotBase(BaseModel):
    material_type: str
    material_form: str
    mfi: float
    density: float
    quantity_tons: float
    selling_price_usd: float
    carbon_score: str
    custom_fields: Optional[dict] = {}

class GuaranteedLotCreate(GuaranteedLotBase):
    original_offer_id: int

class GuaranteedLot(GuaranteedLotBase):
    id: int
    original_offer_id: int
    is_active: bool
    seller_name: Optional[str] = None

    class Config:
        from_attributes = True

class GuaranteedLotUpdate(BaseModel):
    selling_price_usd: Optional[float] = None
    custom_fields: Optional[dict] = None
    is_active: Optional[bool] = None

# REQUEST (TALEP YARAT) SCHEMAS
class RequestBase(BaseModel):
    material_type: str
    min_mfi: float
    max_mfi: float
    min_density: float
    max_density: float
    target_quantity_tons: float

class PurchaseRequestCreate(RequestBase):
    pass

class PurchaseRequest(RequestBase):
    id: int
    buyer_id: int
    status: str

    class Config:
        from_attributes = True

# ORDER (ESCROW) SCHEMAS
class OrderBase(BaseModel):
    lot_id: int
    quantity_tons: float
    incoterms: Optional[str] = "EXW"

class OrderCreate(OrderBase):
    pass

class Order(OrderBase):
    id: int
    buyer_id: int
    total_amount_usd: float
    payment_status: str
    created_at: datetime

    class Config:
        from_attributes = True

# MESSAGE SCHEMAS
class MessageCreate(BaseModel):
    conversation_id: Optional[int] = None
    receiver_id: int
    lot_id: Optional[int] = None
    text: str

class MessageResponse(BaseModel):
    id: int
    sender_id: int
    text: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class ConversationResponse(BaseModel):
    id: int
    lot_id: Optional[int] = None
    buyer_id: int
    seller_id: int
    created_at: datetime
    last_message: Optional[str] = None
    other_user_name: Optional[str] = None
    
    class Config:
        from_attributes = True
