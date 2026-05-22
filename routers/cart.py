from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas

from database import get_db
from auth.oauth2 import get_current_user


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

    if product.stock < cart.quantity:
        raise HTTPException(
            status_code=400,
            detail="Not enough stock available"
        )

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

    product.stock += cart_item.quantity
    product.stock -= update_data.quantity
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

    total_price = 0.0
    total_quantity = 0

    for item in cart_items:
        product = db.query(models.Product).filter(
            models.Product.id == item.product_id
        ).first()

        if not product or product.stock < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for {item.product_name}"
            )

        total_price += item.price * item.quantity
        total_quantity += item.quantity

    discount_amount = 0.0
    coupon_code = checkout.coupon_code

    if coupon_code:
        coupon = db.query(models.Coupon).filter(
            models.Coupon.code == coupon_code,
            models.Coupon.active == True
        ).first()

        if not coupon:
            raise HTTPException(
                status_code=400,
                detail="Invalid coupon code"
            )

        if coupon.expires_at is not None and coupon.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=400,
                detail="Coupon has expired"
            )

        if coupon.max_uses and coupon.used_count >= coupon.max_uses:
            raise HTTPException(
                status_code=400,
                detail="Coupon usage limit reached"
            )

        discount_amount = total_price * (coupon.discount_percent / 100)
        total_price = max(total_price - discount_amount, 0.0)
        coupon.used_count += 1

    order_description = ", ".join(
        f"{item.product_name} x{item.quantity}" for item in cart_items
    )

    new_order = models.Order(
        product_name=order_description,
        quantity=total_quantity,
        total_price=total_price,
        discount_amount=discount_amount,
        coupon_code=coupon_code,
        customer=current_user["email"]
    )

    for item in cart_items:
        product = db.query(models.Product).filter(
            models.Product.id == item.product_id
        ).first()
        product.stock -= item.quantity
        db.delete(item)

    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    return {
        "message": "Checkout complete",
        "order_id": new_order.id,
        "total_price": total_price,
        "discount_amount": discount_amount,
        "items": order_description
    }


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