from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship

from .database import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    # Geçerli roller: Admin / Business Owner / Sales Manager / Inventory Staff
    role = Column(String, default="Inventory Staff", nullable=False)
    created_at = Column(DateTime, default=utcnow)


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    orders = relationship("Order", back_populates="customer")
    messages = relationship("ChatMessage", back_populates="customer")


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=True)

    products = relationship("Product", back_populates="supplier")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    stock_quantity = Column(Integer, default=0)
    critical_stock_level = Column(Integer, default=10)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    supplier = relationship("Supplier", back_populates="products")
    order_details = relationship("OrderDetail", back_populates="product")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    status = Column(String, default="Pending")  # Pending, Preparing, Completed, Cancelled
    total_amount = Column(Float, default=0.0)
    tracking_no = Column(String, nullable=True)
    shipping_carrier = Column(String, nullable=True)
    order_date = Column(DateTime, default=utcnow)
    created_at = Column(DateTime, default=utcnow)
    estimated_delivery = Column(DateTime, nullable=True)

    customer = relationship("Customer", back_populates="orders")
    details = relationship("OrderDetail", back_populates="order", cascade="all, delete-orphan")


class OrderDetail(Base):
    __tablename__ = "order_details"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)

    order = relationship("Order", back_populates="details")
    product = relationship("Product", back_populates="order_details")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    # customer_id zorunlu — staff/anonim mesajlar (customer_id=None) DB'ye yazılmaz,
    # `agent._save_message` bu durumda short-circuit eder. Staff chat'leri farklı
    # kullanıcılar arasında karıştırmamak için kasıtlı stateless tutulur.
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    role = Column(String, nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow)

    customer = relationship("Customer", back_populates="messages")


ORDER_STATUSES = ("Pending", "Preparing", "Completed", "Cancelled")
