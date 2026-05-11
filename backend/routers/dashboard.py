"""
Frontend `GET /dashboard` flat istatistik bekliyor:
  { total_products, total_orders, pending_orders, preparing_orders,
    completed_orders, low_stock_products, today_orders }

"Today" filtresi: dashboard.html ve script.js'te hardcoded "2026-05-09" var.
Biz dinamik olarak datetime.now().date() kullanıyoruz; demo gününde seed
o tarihe set ederseniz today_orders sayısı doğru çıkar.
"""
from typing import Annotated
from datetime import datetime, timezone

from fastapi import APIRouter
from sqlalchemy import func

from ..database import db_dependency
from ..models import Order, Product
from .auth import user_dependency

router = APIRouter(tags=["Dashboard"])






@router.get("/dashboard")
def get_dashboard(user: user_dependency, db: db_dependency):
    total_products = db.query(func.count(Product.id)).scalar() or 0
    total_orders = db.query(func.count(Order.id)).scalar() or 0
    pending = db.query(func.count(Order.id)).filter(Order.status == "Pending").scalar() or 0
    preparing = db.query(func.count(Order.id)).filter(Order.status == "Preparing").scalar() or 0
    completed = db.query(func.count(Order.id)).filter(Order.status == "Completed").scalar() or 0
    low_stock = (
        db.query(func.count(Product.id))
        .filter(Product.stock_quantity <= Product.critical_stock_level)
        .scalar()
        or 0
    )

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    today_orders = 0
    for o in db.query(Order).all():
        if o.order_date and o.order_date.strftime("%Y-%m-%d") == today_str:
            today_orders += 1

    return {
        "total_products": total_products,
        "total_orders": total_orders,
        "pending_orders": pending,
        "preparing_orders": preparing,
        "completed_orders": completed,
        "low_stock_products": low_stock,
        "today_orders": today_orders,
    }
