from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Path
from starlette import status

from ..database import db_dependency
from ..models import Product
from ..schemas import ProductCreate
from .auth import user_dependency, require_roles, ROLE_ADMIN, ROLE_BUSINESS_OWNER

router = APIRouter(tags=["Products"])






def _serialize(p: Product) -> dict:
    return {
        "product_id": p.id,
        "product_name": p.name,
        "category": p.category,
        "price": p.price,
        "stock_quantity": p.stock_quantity,
        "critical_stock_level": p.critical_stock_level,
    }


@router.get("/products")
def list_products(user: user_dependency, db: db_dependency):
    return [_serialize(p) for p in db.query(Product).order_by(Product.id).all()]


@router.post("/products", status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    db: db_dependency,
    user: dict = Depends(require_roles(ROLE_ADMIN, ROLE_BUSINESS_OWNER)),
):
    product = Product(
        name=payload.product_name,
        category=payload.category,
        price=payload.price,
        stock_quantity=payload.stock_quantity,
        critical_stock_level=payload.critical_stock_level,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return {"message": "Product created successfully", "product": _serialize(product)}


@router.put("/products/{product_id}")
def update_product(
    db: db_dependency,
    payload: ProductCreate,
    product_id: int = Path(gt=0),
    user: dict = Depends(require_roles(ROLE_ADMIN, ROLE_BUSINESS_OWNER)),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    product.name = payload.product_name
    product.category = payload.category
    product.price = payload.price
    product.stock_quantity = payload.stock_quantity
    product.critical_stock_level = payload.critical_stock_level
    db.commit()
    db.refresh(product)
    return {"message": "Product updated successfully", "product": _serialize(product)}


@router.delete("/products/{product_id}")
def delete_product(
    db: db_dependency,
    product_id: int = Path(gt=0),
    user: dict = Depends(require_roles(ROLE_ADMIN, ROLE_BUSINESS_OWNER)),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    db.delete(product)
    db.commit()
    return {"message": "Product deleted successfully"}
