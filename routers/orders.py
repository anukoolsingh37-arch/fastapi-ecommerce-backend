from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas

from database import get_db
from auth.oauth2 import get_current_user

router = APIRouter(
    prefix="/orders",
    tags=["Orders"]
)


@router.post("/")
def create_order(
    order: schemas.Order,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    product = db.query(models.Product).filter(
        models.Product.title == order.product_name
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    if product.stock < order.quantity:
        raise HTTPException(
            status_code=400,
            detail="Not enough stock available"
        )

    total_price = product.price * order.quantity
    discount_amount = 0.0

    if order.coupon_code:
        coupon = db.query(models.Coupon).filter(
            models.Coupon.code == order.coupon_code,
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

    new_order = models.Order(
        product_name=product.title,
        quantity=order.quantity,
        total_price=total_price,
        discount_amount=discount_amount,
        coupon_code=order.coupon_code,
        customer=current_user["email"]
    )

    product.stock -= order.quantity

    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    return {
        "message": "Order placed successfully",
        "remaining_stock": product.stock,
        "order": new_order
    }


@router.get("/")
def get_orders(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    orders = db.query(models.Order).filter(
        models.Order.customer == current_user["email"]
    ).all()

    return orders