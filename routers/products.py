from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from auth.oauth2 import get_current_user

import models
import schemas

router = APIRouter(
    tags=["Products"]
)


@router.post("/products")
def create_product(
    product: schemas.Product,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):

    new_product = models.Product(
        title=product.title,
        description=product.description,
        price=product.price,
        stock=product.stock,
        image=product.image
    )

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return {
        "message": "Product created successfully",
        "product": new_product
    }


@router.get("/products")
def get_products(
    page: int = 1,
    limit: int = 5,
    db: Session = Depends(get_db)
):

    skip = (page - 1) * limit

    products = db.query(models.Product).offset(skip).limit(limit).all()

    return {
        "page": page,
        "limit": limit,
        "products": products
    }


@router.get("/products/search")
def search_products(
    name: str = None,
    min_price: float = None,
    max_price: float = None,
    sort_by: str = None,
    db: Session = Depends(get_db)
):

    query = db.query(models.Product)

    if name:
        query = query.filter(
            models.Product.title.ilike(f"%{name}%")
        )

    if min_price is not None:
        query = query.filter(
            models.Product.price >= min_price
        )

    if max_price is not None:
        query = query.filter(
            models.Product.price <= max_price
        )

    if sort_by == "low":
        query = query.order_by(
            models.Product.price.asc()
        )

    elif sort_by == "high":
        query = query.order_by(
            models.Product.price.desc()
        )

    products = query.all()

    return products


@router.get("/products/{product_id}")
def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):

    product = db.query(models.Product).filter(
        models.Product.id == product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    return product


@router.put("/products/{product_id}")
def update_product(
    product_id: int,
    product: schemas.Product,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):

    existing_product = db.query(models.Product).filter(
        models.Product.id == product_id
    ).first()

    if not existing_product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    existing_product.title = product.title
    existing_product.description = product.description
    existing_product.price = product.price
    existing_product.stock = product.stock
    existing_product.image = product.image

    db.commit()

    return {
        "message": "Product updated successfully"
    }


@router.delete("/products/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):

    existing_product = db.query(models.Product).filter(
        models.Product.id == product_id
    ).first()

    if not existing_product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    db.delete(existing_product)
    db.commit()

    return {
        "message": "Product deleted successfully"
    }


@router.get("/products/{product_id}/stock")
def get_product_stock(
    product_id: int,
    db: Session = Depends(get_db)
):
    product = db.query(models.Product).filter(
        models.Product.id == product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    return {
        "product_id": product.id,
        "stock": product.stock
    }


@router.patch("/products/{product_id}/stock")
def update_product_stock(
    product_id: int,
    inventory: schemas.InventoryUpdate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    product = db.query(models.Product).filter(
        models.Product.id == product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    product.stock = inventory.stock
    db.commit()

    return {
        "message": "Product stock updated successfully",
        "product_id": product.id,
        "stock": product.stock
    }


@router.get("/summary")
def order_summary(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    orders = db.query(models.Order).filter(
        models.Order.customer == current_user["email"]
    ).all()

    total_orders = len(orders)

    total_spent = sum(
        order.total_price for order in orders
    )

    return {
        "total_orders": total_orders,
        "total_spent": total_spent,
        "orders": orders
    }
