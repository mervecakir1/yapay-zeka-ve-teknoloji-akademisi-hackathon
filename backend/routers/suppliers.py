"""
Supplier endpoints.

This router is used by the frontend Suppliers page.
It lists suppliers and returns the products linked to each supplier.
It also supports creating, updating, and deleting suppliers.
"""

from fastapi import APIRouter, Depends, HTTPException, Path
from starlette import status

from ..database import db_dependency
from ..models import Supplier, Product
from ..schemas import SupplierCreate
from .auth import (
    user_dependency,
    require_roles,
    ROLE_ADMIN,
    ROLE_BUSINESS_OWNER,
)

router = APIRouter(tags=["Suppliers"])


def _serialize(supplier: Supplier) -> dict:
    return {
        "supplier_id": supplier.id,
        "name": supplier.name,
        "email": supplier.email,
        "phone": supplier.phone,
        "products_count": len(supplier.products),
        "products": [
            {
                "product_id": product.id,
                "product_name": product.name,
                "stock_quantity": product.stock_quantity,
            }
            for product in supplier.products
        ],
    }


def _link_products_to_supplier(db, supplier: Supplier, product_ids: list[int]):
    """
    Links selected products to the given supplier.
    Product IDs come from the frontend add/update supplier forms.
    """

    clean_product_ids = list(dict.fromkeys(product_ids or []))

    if not clean_product_ids:
        return

    products = db.query(Product).filter(Product.id.in_(clean_product_ids)).all()

    found_ids = {product.id for product in products}
    missing_ids = [
        product_id
        for product_id in clean_product_ids
        if product_id not in found_ids
    ]

    if missing_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Products not found: {missing_ids}",
        )

    for product in products:
        product.supplier_id = supplier.id


@router.get("/suppliers")
def list_suppliers(user: user_dependency, db: db_dependency):
    """
    Returns all suppliers with their linked products.
    """

    suppliers = db.query(Supplier).order_by(Supplier.id).all()
    return [_serialize(supplier) for supplier in suppliers]


@router.get("/suppliers/{supplier_id}")
def get_supplier(
    user: user_dependency,
    db: db_dependency,
    supplier_id: int = Path(gt=0),
):
    """
    Returns a single supplier by ID.
    """

    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()

    if supplier is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found.",
        )

    return _serialize(supplier)


@router.post("/suppliers", status_code=status.HTTP_201_CREATED)
def create_supplier(
    payload: SupplierCreate,
    db: db_dependency,
    user: dict = Depends(require_roles(ROLE_ADMIN, ROLE_BUSINESS_OWNER)),
):
    """
    Creates a new supplier and links selected products to it.
    The supplier ID is generated automatically by the database.
    """

    supplier = Supplier(
        name=payload.name.strip(),
        email=payload.email.strip(),
        phone=payload.phone.strip() if payload.phone else None,
    )

    db.add(supplier)
    db.flush()

    _link_products_to_supplier(db, supplier, payload.product_ids)

    db.commit()
    db.refresh(supplier)

    return {
        "message": "Supplier created successfully.",
        "supplier": _serialize(supplier),
    }


@router.put("/suppliers/{supplier_id}")
def update_supplier(
    payload: SupplierCreate,
    db: db_dependency,
    supplier_id: int = Path(gt=0),
    user: dict = Depends(require_roles(ROLE_ADMIN, ROLE_BUSINESS_OWNER)),
):
    """
    Updates supplier email, phone and linked products.
    Supplier name is kept from the existing supplier record unless frontend sends the same name.
    """

    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()

    if supplier is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found.",
        )

    supplier.name = payload.name.strip()
    supplier.email = payload.email.strip()
    supplier.phone = payload.phone.strip() if payload.phone else None

    # Remove old product links for this supplier.
    for product in list(supplier.products):
        product.supplier_id = None

    # Link selected products again.
    _link_products_to_supplier(db, supplier, payload.product_ids)

    db.commit()
    db.refresh(supplier)

    return {
        "message": "Supplier updated successfully.",
        "supplier": _serialize(supplier),
    }


@router.delete("/suppliers/{supplier_id}")
def delete_supplier(
    db: db_dependency,
    supplier_id: int = Path(gt=0),
    user: dict = Depends(require_roles(ROLE_ADMIN, ROLE_BUSINESS_OWNER)),
):
    """
    Deletes a supplier.
    Before deleting, linked products are detached from the supplier.
    """

    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()

    if supplier is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found.",
        )

    # Detach products before deleting the supplier.
    for product in list(supplier.products):
        product.supplier_id = None

    db.delete(supplier)
    db.commit()

    return {
        "message": "Supplier deleted successfully."
    }