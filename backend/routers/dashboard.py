"""
Dashboard endpoint — frontend için flat istatistik döner.

Response:
  { total_products, total_orders, pending_orders, preparing_orders,
    completed_orders, low_stock_products, today_orders,
    today_completed, today_revenue, ai_brief }

"today" filtresi sunucu UTC tarihine göre dinamik.
ai_brief AI servisinden gelir (Gemini açıksa) veya kural-tabanlı fallback.
"""
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter
from sqlalchemy import func, and_

from ..database import db_dependency
from ..models import Order, Product
from .auth import user_dependency
from ai.dashboard_brief import generate_brief

router = APIRouter(tags=["Dashboard"])


def _today_range():
    """Bugünün başlangıcı ve bitişi (UTC)."""
    now = datetime.now(timezone.utc)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return start, end


@router.get("/dashboard")
def get_dashboard(user: user_dependency, db: db_dependency):
    today_start, today_end = _today_range()

    # Genel sayılar
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

    # Bugünün siparişleri (toplam)
    today_orders = (
        db.query(func.count(Order.id))
        .filter(and_(Order.order_date >= today_start, Order.order_date < today_end))
        .scalar()
        or 0
    )

    # Bugün tamamlanan siparişler (kargolanma proxy'si)
    today_completed = (
        db.query(func.count(Order.id))
        .filter(Order.status == "Completed")
        .filter(and_(Order.order_date >= today_start, Order.order_date < today_end))
        .scalar()
        or 0
    )

    # Bugünün cirosu — iptal edilmemiş siparişlerin toplamı
    today_revenue = (
        db.query(func.coalesce(func.sum(Order.total_amount), 0.0))
        .filter(Order.status != "Cancelled")
        .filter(and_(Order.order_date >= today_start, Order.order_date < today_end))
        .scalar()
        or 0.0
    )
    today_revenue = float(today_revenue)

    stats = {
        "total_products": total_products,
        "total_orders": total_orders,
        "pending_orders": pending,
        "preparing_orders": preparing,
        "completed_orders": completed,
        "low_stock_products": low_stock,
        "today_orders": today_orders,
        "today_completed": today_completed,
        "today_revenue": today_revenue,
    }

    # AI brief — Gemini açıksa onunla, değilse kural-tabanlı fallback
    stats["ai_brief"] = generate_brief({
        "pending_orders": pending,
        "preparing_orders": preparing,
        "shipped_today": today_completed,
        "low_stock_count": low_stock,
        "today_revenue": today_revenue,
    })

    return stats
