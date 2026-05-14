from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas

from database import SessionLocal
from auth.oauth2 import get_current_user


router = APIRouter(
    prefix="/cart",
    tags=["Cart"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/")
def add_to_cart(
    cart: schemas.CartBase,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    new_cart = models.Cart(
        product_name=cart.product_name,
        quantity=cart.quantity,
        price=cart.price,
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