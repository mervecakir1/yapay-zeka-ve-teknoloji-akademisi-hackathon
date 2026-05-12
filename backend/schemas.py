from typing import Optional
from pydantic import BaseModel, Field


# ===== User / Auth =====

class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: str
    password: str = Field(min_length=4)
    role: str = "Inventory Staff"


class LoginRequest(BaseModel):
    email: str
    password: str


# ===== Product =====

class ProductCreate(BaseModel):
    product_name: str = Field(min_length=2, max_length=150)
    category: str
    price: float = Field(gt=0)
    stock_quantity: int = Field(ge=0)
    critical_stock_level: int = Field(ge=0, default=10)


# ===== Order =====

class OrderCreate(BaseModel):
    customer_name: str
    customer_email: str
    customer_phone: Optional[str] = None
    product_id: int
    quantity: int = Field(gt=0)
    order_date: str
    order_status: str
    total_price: float


class OrderStatusUpdate(BaseModel):
    order_status: str
    tracking_no: Optional[str] = None
    shipping_carrier: Optional[str] = None


# ===== Supplier =====

class SupplierCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    email: str
    phone: Optional[str] = None
    product_ids: list[int] = Field(default_factory=list)


# ===== Chat =====

class ChatRequest(BaseModel):
    customer_id: Optional[int] = None
    message: str = Field(min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    reply: str
    used_tools: list[str] = []


# ===== Inventory =====

class InventoryUpdate(BaseModel):
    current_stock: int
    critical_level: int


# ===== Supplier Email Draft =====

class SupplierEmailDraft(BaseModel):
    subject: str
    body: str
    recipient: str
    product_id: int