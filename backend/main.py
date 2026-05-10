from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import SessionLocal
from models import User, Customer, Product, Order, OrderDetail, Inventory


app = FastAPI(title="AI E-Commerce Backend API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===============================
# Database Session
# ===============================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ===============================
# Request Models
# ===============================

class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: str


class LoginRequest(BaseModel):
    email: str
    password: str


class ProductCreate(BaseModel):
    product_name: str
    category: str
    price: float
    stock_quantity: int
    critical_stock_level: int


class ProductUpdate(BaseModel):
    product_name: str
    category: str
    price: float
    stock_quantity: int
    critical_stock_level: int


class OrderCreate(BaseModel):
    customer_name: str
    customer_email: str
    customer_phone: Optional[str] = None
    product_id: int
    quantity: int
    order_date: str
    order_status: str
    total_price: float


class OrderStatusUpdate(BaseModel):
    order_status: str


class InventoryUpdate(BaseModel):
    current_stock: int
    critical_level: int


# ===============================
# Home
# ===============================

@app.get("/")
def home():
    return {
        "message": "AI E-Commerce Backend API is running"
    }


# ===============================
# Users / Register / Login
# ===============================

@app.get("/users")
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()

    return [
        {
            "user_id": user.user_id,
            "name": user.name,
            "email": user.email,
            "role": user.role
        }
        for user in users
    ]


@app.post("/users")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user.email).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already exists.")

    new_user = User(
        name=user.name,
        email=user.email,
        password=user.password,
        role=user.role
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User created successfully",
        "user": {
            "user_id": new_user.user_id,
            "name": new_user.name,
            "email": new_user.email,
            "role": new_user.role
        }
    }


@app.post("/login")
def login_user(login_data: LoginRequest, db: Session = Depends(get_db)):
    user = (
        db.query(User)
        .filter(
            User.email == login_data.email,
            User.password == login_data.password
        )
        .first()
    )

    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    return {
        "message": "Login successful",
        "user": {
            "user_id": user.user_id,
            "name": user.name,
            "email": user.email,
            "role": user.role
        }
    }


@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = (
        db.query(User)
        .filter(User.user_id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    db.delete(user)
    db.commit()

    return {
        "message": "User deleted successfully"
    }


# ===============================
# Products
# ===============================

@app.get("/products")
def get_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()

    return [
        {
            "product_id": product.product_id,
            "product_name": product.product_name,
            "category": product.category,
            "price": product.price,
            "stock_quantity": product.stock_quantity,
            "critical_stock_level": product.critical_stock_level
        }
        for product in products
    ]


@app.post("/products")
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    new_product = Product(
        product_name=product.product_name,
        category=product.category,
        price=product.price,
        stock_quantity=product.stock_quantity,
        critical_stock_level=product.critical_stock_level
    )

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    new_inventory = Inventory(
        product_id=new_product.product_id,
        current_stock=new_product.stock_quantity,
        critical_level=new_product.critical_stock_level,
        last_updated=datetime.now()
    )

    db.add(new_inventory)
    db.commit()
    db.refresh(new_inventory)

    return {
        "message": "Product created successfully",
        "product": {
            "product_id": new_product.product_id,
            "product_name": new_product.product_name,
            "category": new_product.category,
            "price": new_product.price,
            "stock_quantity": new_product.stock_quantity,
            "critical_stock_level": new_product.critical_stock_level
        }
    }


@app.put("/products/{product_id}")
def update_product(product_id: int, product: ProductUpdate, db: Session = Depends(get_db)):
    existing_product = (
        db.query(Product)
        .filter(Product.product_id == product_id)
        .first()
    )

    if not existing_product:
        raise HTTPException(status_code=404, detail="Product not found.")

    existing_product.product_name = product.product_name
    existing_product.category = product.category
    existing_product.price = product.price
    existing_product.stock_quantity = product.stock_quantity
    existing_product.critical_stock_level = product.critical_stock_level

    inventory_item = (
        db.query(Inventory)
        .filter(Inventory.product_id == product_id)
        .first()
    )

    if inventory_item:
        inventory_item.current_stock = product.stock_quantity
        inventory_item.critical_level = product.critical_stock_level
        inventory_item.last_updated = datetime.now()

    db.commit()
    db.refresh(existing_product)

    return {
        "message": "Product updated successfully",
        "product": {
            "product_id": existing_product.product_id,
            "product_name": existing_product.product_name,
            "category": existing_product.category,
            "price": existing_product.price,
            "stock_quantity": existing_product.stock_quantity,
            "critical_stock_level": existing_product.critical_stock_level
        }
    }


@app.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = (
        db.query(Product)
        .filter(Product.product_id == product_id)
        .first()
    )

    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")

    related_order_detail = (
        db.query(OrderDetail)
        .filter(OrderDetail.product_id == product_id)
        .first()
    )

    if related_order_detail:
        raise HTTPException(
            status_code=400,
            detail="This product is used in an order and cannot be deleted."
        )

    inventory_item = (
        db.query(Inventory)
        .filter(Inventory.product_id == product_id)
        .first()
    )

    if inventory_item:
        db.delete(inventory_item)

    db.delete(product)
    db.commit()

    return {
        "message": "Product deleted successfully"
    }


# ===============================
# Orders
# ===============================

@app.get("/orders")
def get_orders(db: Session = Depends(get_db)):
    orders = db.query(Order).join(Customer).all()

    result = []

    for order in orders:
        first_detail = (
            db.query(OrderDetail)
            .filter(OrderDetail.order_id == order.order_id)
            .first()
        )

        product_name = "-"
        quantity = 0

        if first_detail:
            quantity = first_detail.quantity

            product = (
                db.query(Product)
                .filter(Product.product_id == first_detail.product_id)
                .first()
            )

            if product:
                product_name = product.product_name

        result.append(
            {
                "order_id": order.order_id,
                "customer_name": order.customer.name,
                "product_name": product_name,
                "quantity": quantity,
                "order_date": order.order_date.strftime("%Y-%m-%d"),
                "order_status": order.order_status,
                "total_price": order.total_amount
            }
        )

    return result


@app.post("/orders")
def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    allowed_statuses = ["Pending", "Preparing", "Completed", "Cancelled"]

    if order.order_status not in allowed_statuses:
        raise HTTPException(status_code=400, detail="Invalid order status.")

    product = (
        db.query(Product)
        .filter(Product.product_id == order.product_id)
        .first()
    )

    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")

    if order.order_status != "Cancelled" and product.stock_quantity < order.quantity:
        raise HTTPException(status_code=400, detail="Not enough stock for this product.")

    customer = (
        db.query(Customer)
        .filter(Customer.email == order.customer_email)
        .first()
    )

    if not customer:
        customer = Customer(
            name=order.customer_name,
            email=order.customer_email,
            phone=order.customer_phone
        )

        db.add(customer)
        db.commit()
        db.refresh(customer)

    new_order = Order(
        customer_id=customer.customer_id,
        order_date=datetime.strptime(order.order_date, "%Y-%m-%d"),
        order_status=order.order_status,
        total_amount=order.total_price
    )

    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    order_detail = OrderDetail(
        order_id=new_order.order_id,
        product_id=product.product_id,
        quantity=order.quantity,
        unit_price=product.price
    )

    db.add(order_detail)

    if order.order_status != "Cancelled":
        product.stock_quantity -= order.quantity

        inventory_item = (
            db.query(Inventory)
            .filter(Inventory.product_id == product.product_id)
            .first()
        )

        if inventory_item:
            inventory_item.current_stock = product.stock_quantity
            inventory_item.last_updated = datetime.now()

    db.commit()
    db.refresh(order_detail)

    return {
        "message": "Order created successfully",
        "order": {
            "order_id": new_order.order_id,
            "customer_name": customer.name,
            "product_name": product.product_name,
            "quantity": order.quantity,
            "order_status": new_order.order_status,
            "total_price": new_order.total_amount
        }
    }


@app.put("/orders/{order_id}/status")
def update_order_status(order_id: int, status_data: OrderStatusUpdate, db: Session = Depends(get_db)):
    allowed_statuses = ["Pending", "Preparing", "Completed"]

    if status_data.order_status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail="Invalid order status. Use /orders/{order_id}/cancel to cancel an order."
        )

    order = (
        db.query(Order)
        .filter(Order.order_id == order_id)
        .first()
    )

    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")

    if order.order_status == "Cancelled":
        raise HTTPException(status_code=400, detail="Cancelled orders cannot be updated.")

    order.order_status = status_data.order_status

    db.commit()
    db.refresh(order)

    return {
        "message": "Order status updated successfully",
        "order_id": order.order_id,
        "order_status": order.order_status
    }


@app.put("/orders/{order_id}/cancel")
def cancel_order(order_id: int, db: Session = Depends(get_db)):
    order = (
        db.query(Order)
        .filter(Order.order_id == order_id)
        .first()
    )

    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")

    if order.order_status == "Cancelled":
        raise HTTPException(status_code=400, detail="Order is already cancelled.")

    order_details = (
        db.query(OrderDetail)
        .filter(OrderDetail.order_id == order_id)
        .all()
    )

    for detail in order_details:
        product = (
            db.query(Product)
            .filter(Product.product_id == detail.product_id)
            .first()
        )

        if product:
            product.stock_quantity += detail.quantity

            inventory_item = (
                db.query(Inventory)
                .filter(Inventory.product_id == product.product_id)
                .first()
            )

            if inventory_item:
                inventory_item.current_stock = product.stock_quantity
                inventory_item.last_updated = datetime.now()

    order.order_status = "Cancelled"

    db.commit()
    db.refresh(order)

    return {
        "message": "Order cancelled successfully and stock restored.",
        "order_id": order.order_id,
        "order_status": order.order_status
    }


# ===============================
# Inventory
# ===============================

@app.get("/inventory")
def get_inventory(db: Session = Depends(get_db)):
    inventory_items = db.query(Inventory).join(Product).all()

    return [
        {
            "inventory_id": item.inventory_id,
            "product_id": item.product_id,
            "product_name": item.product.product_name,
            "current_stock": item.current_stock,
            "critical_level": item.critical_level,
            "last_updated": item.last_updated.strftime("%Y-%m-%d")
        }
        for item in inventory_items
    ]


@app.put("/inventory/{product_id}")
def update_inventory(product_id: int, inventory_data: InventoryUpdate, db: Session = Depends(get_db)):
    product = (
        db.query(Product)
        .filter(Product.product_id == product_id)
        .first()
    )

    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")

    inventory_item = (
        db.query(Inventory)
        .filter(Inventory.product_id == product_id)
        .first()
    )

    if not inventory_item:
        inventory_item = Inventory(
            product_id=product_id,
            current_stock=inventory_data.current_stock,
            critical_level=inventory_data.critical_level,
            last_updated=datetime.now()
        )
        db.add(inventory_item)
    else:
        inventory_item.current_stock = inventory_data.current_stock
        inventory_item.critical_level = inventory_data.critical_level
        inventory_item.last_updated = datetime.now()

    product.stock_quantity = inventory_data.current_stock
    product.critical_stock_level = inventory_data.critical_level

    db.commit()
    db.refresh(inventory_item)

    return {
        "message": "Inventory updated successfully",
        "product_id": product_id,
        "current_stock": inventory_item.current_stock,
        "critical_level": inventory_item.critical_level
    }


# ===============================
# Dashboard
# ===============================

@app.get("/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    orders = db.query(Order).all()

    low_stock_products = [
        product for product in products
        if product.stock_quantity <= product.critical_stock_level
    ]

    pending_orders = [
        order for order in orders
        if order.order_status == "Pending"
    ]

    preparing_orders = [
        order for order in orders
        if order.order_status == "Preparing"
    ]

    completed_orders = [
        order for order in orders
        if order.order_status == "Completed"
    ]

    today_orders = [
        order for order in orders
        if order.order_date.strftime("%Y-%m-%d") == "2026-05-09"
    ]

    return {
        "total_products": len(products),
        "total_orders": len(orders),
        "pending_orders": len(pending_orders),
        "preparing_orders": len(preparing_orders),
        "completed_orders": len(completed_orders),
        "low_stock_products": len(low_stock_products),
        "today_orders": len(today_orders)
    }