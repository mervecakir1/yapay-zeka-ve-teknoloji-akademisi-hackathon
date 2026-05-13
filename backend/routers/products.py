from fastapi import APIRouter, Depends, HTTPException, Path
from starlette import status

from ..database import db_dependency
from ..models import Product
from ..schemas import ProductCreate
from .auth import (
    user_dependency,
    require_roles,
    ROLE_ADMIN,
    ROLE_BUSINESS_OWNER,
)

router = APIRouter(tags=["Products"])


def _serialize(product: Product) -> dict:
    return {
        "product_id": product.id,
        "product_name": product.name,
        "category": product.category,
        "price": product.price,
        "stock_quantity": product.stock_quantity,
        "critical_stock_level": product.critical_stock_level,
    }


@router.get("/products")
def list_products(user: user_dependency, db: db_dependency):
    """
    Returns all products.
    """

    products = db.query(Product).order_by(Product.id).all()

    return [
        _serialize(product)
        for product in products
    ]


@router.post("/products", status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    db: db_dependency,
    user: dict = Depends(require_roles(ROLE_ADMIN, ROLE_BUSINESS_OWNER)),
):
    """
    Creates a new product.
    """

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

    return {
        "message": "Product created successfully.",
        "product": _serialize(product),
    }


@router.put("/products/{product_id}")
def update_product(
    payload: ProductCreate,
    db: db_dependency,
    product_id: int = Path(gt=0),
    user: dict = Depends(require_roles(ROLE_ADMIN, ROLE_BUSINESS_OWNER)),
):
    """
    Updates a product.

    Frontend update modal only changes:
    - price
    - stock_quantity
    - critical_stock_level

    Product name and category are sent back unchanged by the frontend.
    """

    product = db.query(Product).filter(Product.id == product_id).first()

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )

    product.name = payload.product_name
    product.category = payload.category
    product.price = payload.price
    product.stock_quantity = payload.stock_quantity
    product.critical_stock_level = payload.critical_stock_level

    db.commit()
    db.refresh(product)

    return {
        "message": "Product updated successfully.",
        "product": _serialize(product),
    }


@router.delete("/products/{product_id}")
def delete_product(
    db: db_dependency,
    product_id: int = Path(gt=0),
    user: dict = Depends(require_roles(ROLE_ADMIN, ROLE_BUSINESS_OWNER)),
):
    """
    Deletes a product by product ID.

    Frontend Delete button uses this endpoint.
    """

    product = db.query(Product).filter(Product.id == product_id).first()

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )

    db.delete(product)
    db.commit()

    return {
        "message": "Product deleted successfully."
    }