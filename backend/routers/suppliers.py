"""
Suppliers (tedarikçi) endpoint'leri. Frontend bunu Suppliers sayfasında listeler.
Tedarikçi başına bağlı ürünleri de döner.
"""
from typing import Annotated
from fastapi import APIRouter, HTTPException, Path
from starlette import status

from ..database import db_dependency
from ..models import Supplier
from .auth import user_dependency

router = APIRouter(tags=["Suppliers"])






def _serialize(s: Supplier) -> dict:
    return {
        "supplier_id": s.id,
        "name": s.name,
        "email": s.email,
        "phone": s.phone,
        "products_count": len(s.products),
        "products": [{"product_id": p.id, "product_name": p.name, "stock_quantity": p.stock_quantity} for p in s.products],
    }


@router.get("/suppliers")
def list_suppliers(user: user_dependency, db: db_dependency):
    return [_serialize(s) for s in db.query(Supplier).order_by(Supplier.id).all()]


@router.get("/suppliers/{supplier_id}")
def get_supplier(user: user_dependency, db: db_dependency, supplier_id: int = Path(gt=0)):
    s = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if s is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found.")
    return _serialize(s)
