from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas

from database import get_db
from auth.oauth2 import get_current_user
from .order_utils import create_order_from_items


router = APIRouter(
    prefix="/cart",
    tags=["Cart"]
)


@router.post("/")
def add_to_cart(
    cart: schemas.CartBase,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    product = db.query(models.Product).filter(
        models.Product.id == cart.product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    if cart.quantity < 1:
        raise HTTPException(
            status_code=400,
            detail="Quantity must be at least 1"
        )

    existing_cart_item = db.query(models.Cart).filter(
        models.Cart.user_id == current_user["id"],
        models.Cart.product_id == product.id
    ).first()

    if existing_cart_item:
        existing_cart_item.quantity += cart.quantity
        db.commit()
        return {
            "message": "Product quantity updated in cart"
        }

    new_cart = models.Cart(
        product_id=product.id,
        product_name=product.title,
        quantity=cart.quantity,
        price=product.price,
        user_id=current_user["id"]
    )

    db.add(new_cart)
    db.commit()

    return {
        "message": "Product added to cart"
    }


@router.get("/")
def get_cart(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    cart_items = db.query(models.Cart).filter(
        models.Cart.user_id == current_user["id"]
    ).all()

    return cart_items


@router.patch("/{cart_id}")
def update_cart_item(
    cart_id: int,
    update_data: schemas.CartUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    cart_item = db.query(models.Cart).filter(
        models.Cart.id == cart_id,
        models.Cart.user_id == current_user["id"]
    ).first()

    if not cart_item:
        raise HTTPException(
            status_code=404,
            detail="Cart item not found"
        )

    product = db.query(models.Product).filter(
        models.Product.id == cart_item.product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    if update_data.quantity < 1:
        raise HTTPException(
            status_code=400,
            detail="Quantity must be at least 1"
        )

    if product.stock + cart_item.quantity < update_data.quantity:
        raise HTTPException(
            status_code=400,
            detail="Not enough stock available"
        )

    # Stock is only decremented at checkout, not on cart updates
    cart_item.quantity = update_data.quantity

    db.commit()
    db.refresh(cart_item)

    return {
        "message": "Cart item updated",
        "cart_item": cart_item
    }


@router.post("/checkout")
def checkout_cart(
    checkout: schemas.CartCheckout,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    cart_items = db.query(models.Cart).filter(
        models.Cart.user_id == current_user["id"]
    ).all()

    if not cart_items:
        raise HTTPException(
            status_code=400,
            detail="Cart is empty"
        )

    items = []
    for item in cart_items:
        product = db.query(models.Product).filter(
            models.Product.id == item.product_id
        ).first()

        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Product {item.product_name} not found"
            )

        items.append({
            "product_id": item.product_id,
            "quantity": item.quantity
        })

    return create_order_from_items(
        db=db,
        current_user=current_user,
        items=items,
        coupon_code=checkout.coupon_code,
        cart_items=cart_items
    )


@router.delete("/{cart_id}")
def remove_cart_item(
    cart_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    cart_item = db.query(models.Cart).filter(
        models.Cart.id == cart_id,
        models.Cart.user_id == current_user["id"]
    ).first()

    if not cart_item:
        raise HTTPException(
            status_code=404,
            detail="Cart item not found"
        )

    db.delete(cart_item)
    db.commit()

    return {
        "message": "Item removed from cart"
    }