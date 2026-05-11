"""
Frontend `GET /inventory` listesi bekliyor:
  [{ product_name, current_stock, critical_level }, ...]

Bizde ayrı Inventory tablosu yok — Product zaten stock_quantity ve
critical_stock_level taşıyor. Bu endpoint Product'tan türetilmiş "view" döner.
"""
from typing import Annotated
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from sqlalchemy import func
from starlette import status

from ..database import db_dependency
from ..models import Product, OrderDetail, Order
from ..schemas import InventoryUpdate, SupplierEmailDraft
from ai.supplier_email import draft_supplier_email
from .auth import user_dependency, require_roles, ROLE_ADMIN, ROLE_BUSINESS_OWNER, ROLE_INVENTORY_STAFF

router = APIRouter(tags=["Inventory"])






def _suggest_order_qty(db: Session, product_id: int, fallback: int) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    total = (
        db.query(func.coalesce(func.sum(OrderDetail.quantity), 0))
        .join(Order, Order.id == OrderDetail.order_id)
        .filter(OrderDetail.product_id == product_id)
        .filter(Order.created_at >= cutoff)
        .scalar()
    )
    if total and total > 0:
        return int(total * 1.5)
    return max(fallback * 3, 10)


@router.get("/inventory")
def list_inventory(user: user_dependency, db: db_dependency):
    products = db.query(Product).order_by(Product.id).all()
    return [
        {
            "inventory_id": p.id,
            "product_id": p.id,
            "product_name": p.name,
            "current_stock": p.stock_quantity,
            "critical_level": p.critical_stock_level,
            "last_updated": p.updated_at.strftime("%Y-%m-%d %H:%M") if p.updated_at else None,
        }
        for p in products
    ]


@router.put("/inventory/{product_id}")
def update_inventory(
    db: db_dependency,
    payload: InventoryUpdate,
    product_id: int = Path(gt=0),
    user: dict = Depends(require_roles(ROLE_ADMIN, ROLE_BUSINESS_OWNER, ROLE_INVENTORY_STAFF)),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    product.stock_quantity = payload.current_stock
    product.critical_stock_level = payload.critical_level
    db.commit()
    db.refresh(product)
    return {
        "message": "Inventory updated successfully",
        "product_id": product.id,
        "current_stock": product.stock_quantity,
        "critical_level": product.critical_stock_level,
    }


@router.post("/inventory/products/{product_id}/draft-supplier-email", response_model=SupplierEmailDraft)
def draft_email_for_product(
    db: db_dependency,
    product_id: int = Path(gt=0),
    user: dict = Depends(require_roles(ROLE_ADMIN, ROLE_BUSINESS_OWNER, ROLE_INVENTORY_STAFF)),
):
    """AI servisi üzerinden tedarikçiye gönderilecek mail taslağı üretir."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    if product.supplier is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product has no supplier.")

    suggested = _suggest_order_qty(db, product.id, product.critical_stock_level)
    return draft_supplier_email(
        product_id=product.id,
        product_name=product.name,
        current_stock=product.stock_quantity,
        critical_level=product.critical_stock_level,
        supplier_name=product.supplier.name,
        supplier_email=product.supplier.email,
        suggested_order_qty=suggested,
    )
