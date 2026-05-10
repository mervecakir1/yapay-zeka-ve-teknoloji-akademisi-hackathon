from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, nullable=False)


class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String)

    orders = relationship("Order", back_populates="customer")


class Product(Base):
    __tablename__ = "products"

    product_id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    stock_quantity = Column(Integer, nullable=False)
    critical_stock_level = Column(Integer, nullable=False)

    order_details = relationship("OrderDetail", back_populates="product")
    inventory = relationship("Inventory", back_populates="product", uselist=False)


class Order(Base):
    __tablename__ = "orders"

    order_id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"))
    order_date = Column(DateTime, default=datetime.utcnow)
    order_status = Column(String, nullable=False)
    total_amount = Column(Float, nullable=False)

    customer = relationship("Customer", back_populates="orders")
    order_details = relationship("OrderDetail", back_populates="order")


class OrderDetail(Base):
    __tablename__ = "order_details"

    order_detail_id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"))
    product_id = Column(Integer, ForeignKey("products.product_id"))
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)

    order = relationship("Order", back_populates="order_details")
    product = relationship("Product", back_populates="order_details")


class Inventory(Base):
    __tablename__ = "inventory"

    inventory_id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.product_id"))
    current_stock = Column(Integer, nullable=False)
    critical_level = Column(Integer, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="inventory")