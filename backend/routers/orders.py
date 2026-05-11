"""
Frontend tek-ürünlü flat sipariş formatı kullanıyor:
  - POST /orders body: {customer_name, customer_email, customer_phone, product_id, quantity, order_date, order_status, total_price}
  - GET /orders response: liste of {order_id, customer_name, product_name, quantity, order_date, order_status, total_price}

DB tarafında Order + OrderDetail kullanmaya devam ediyoruz (esneklik için),
ama API'de frontend'in beklediği gibi tek ürünü düzleştiriyoruz.
"""
from typing import Annotated
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from starlette import status

from ..database import db_dependency
from ..models import Order, OrderDetail, Product, Customer, ORDER_STATUSES
from ..schemas import OrderCreate, OrderStatusUpdate
from .auth import user_dependency, require_roles, ROLE_ADMIN, ROLE_BUSINESS_OWNER, ROLE_SALES_MANAGER

router = APIRouter(tags=["Orders"])






def _serialize_order(db: Session, order: Order) -> dict:
    """İlk OrderDetail'ı seçip flat dict üret — frontend tek ürün bekliyor."""
    first_detail = (
        db.query(OrderDetail)
        .filter(OrderDetail.order_id == order.id)
        .first()
    )
    product_name = "-"
    quantity = 0
    unit_price = 0.0
    if first_detail:
        quantity = first_detail.quantity
        unit_price = first_detail.unit_price
        product = db.query(Product).filter(Product.id == first_detail.product_id).first()
        if product:
            product_name = product.name
    return {
        "order_id": order.id,
        "customer_name": order.customer.name if order.customer else "-",
        "customer_email": order.customer.email if order.customer else None,
        "customer_phone": order.customer.phone if order.customer else None,
        "product_name": product_name,
        "quantity": quantity,
        "unit_price": unit_price,
        "order_date": order.order_date.strftime("%Y-%m-%d") if order.order_date else None,
        "order_status": order.status,
        "total_price": order.total_amount,
        "tracking_no": order.tracking_no,
        "shipping_carrier": order.shipping_carrier,
        "estimated_delivery": order.estimated_delivery.strftime("%Y-%m-%d") if order.estimated_delivery else None,
    }


@router.get("/orders")
def list_orders(user: user_dependency, db: db_dependency):
    rows = db.query(Order).order_by(Order.id.desc()).all()
    return [_serialize_order(db, o) for o in rows]


@router.post("/orders", status_code=status.HTTP_201_CREATED)
def create_order(
    payload: OrderCreate,
    db: db_dependency,
    user: dict = Depends(require_roles(ROLE_ADMIN, ROLE_BUSINESS_OWNER, ROLE_SALES_MANAGER)),
):
    if payload.order_status not in ORDER_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid order status.")

    product = db.query(Product).filter(Product.id == payload.product_id).first()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

    if payload.order_status != "Cancelled" and product.stock_quantity < payload.quantity:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not enough stock for this product.")

    # Customer: var olan email ile eşle, yoksa oluştur
    customer = db.query(Customer).filter(Customer.email == payload.customer_email).first()
    if customer is None:
        customer = Customer(
            name=payload.customer_name,
            email=payload.customer_email,
            phone=payload.customer_phone,
        )
        db.add(customer)
        db.flush()

    try:
        order_date_dt = datetime.strptime(payload.order_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid date format (use YYYY-MM-DD).")

    order = Order(
        customer_id=customer.id,
        order_date=order_date_dt,
        status=payload.order_status,
        total_amount=payload.total_price,
        estimated_delivery=order_date_dt + timedelta(days=3),
    )
    db.add(order)
    db.flush()

    detail = OrderDetail(
        order_id=order.id,
        product_id=product.id,
        quantity=payload.quantity,
        unit_price=product.price,
    )
    db.add(detail)

    if payload.order_status != "Cancelled":
        product.stock_quantity -= payload.quantity

    db.commit()
    db.refresh(order)

    return {"message": "Order created successfully", "order": _serialize_order(db, order)}


@router.put("/orders/{order_id}/status")
def update_order_status(
    db: db_dependency,
    payload: OrderStatusUpdate,
    order_id: int = Path(gt=0),
    user: dict = Depends(require_roles(ROLE_ADMIN, ROLE_BUSINESS_OWNER, ROLE_SALES_MANAGER)),
):
    if payload.order_status not in ("Pending", "Preparing", "Completed"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid status. To cancel, use /orders/{order_id}/cancel.",
        )

    order = db.query(Order).filter(Order.id == order_id).first()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

    if order.status == "Cancelled":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cancelled orders cannot be updated.")

    order.status = payload.order_status
    if payload.tracking_no is not None:
        order.tracking_no = payload.tracking_no
    if payload.shipping_carrier is not None:
        order.shipping_carrier = payload.shipping_carrier
    db.commit()
    db.refresh(order)
    return {
        "message": "Order status updated successfully",
        "order": _serialize_order(db, order),
    }


@router.put("/orders/{order_id}/cancel")
def cancel_order(
    db: db_dependency,
    order_id: int = Path(gt=0),
    user: dict = Depends(require_roles(ROLE_ADMIN, ROLE_BUSINESS_OWNER, ROLE_SALES_MANAGER)),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
    if order.status == "Cancelled":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order is already cancelled.")

    # Stoğu geri yükle
    details = db.query(OrderDetail).filter(OrderDetail.order_id == order_id).all()
    for d in details:
        product = db.query(Product).filter(Product.id == d.product_id).first()
        if product:
            product.stock_quantity += d.quantity

    order.status = "Cancelled"
    db.commit()
    db.refresh(order)
    return {"message": "Order cancelled successfully and stock restored.", "order_id": order.id, "order_status": order.status}
