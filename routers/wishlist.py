from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas

from database import get_db
from auth.oauth2 import get_current_user

router = APIRouter(
    prefix="/wishlist",
    tags=["Wishlist"]
)


@router.post("/")
def add_to_wishlist(
    item: schemas.WishlistItem,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    product = db.query(models.Product).filter(
        models.Product.id == item.product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    new_item = models.Wishlist(
        product_id=product.id,
        product_name=product.title,
        user=current_user["email"]
    )

    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    return {
        "message": "Added to wishlist",
        "wishlist_item": new_item
    }


@router.get("/")
def get_wishlist(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    wishlist = db.query(models.Wishlist).filter(
        models.Wishlist.user == current_user["email"]
    ).all()

    return wishlist


@router.post("/{wishlist_id}/move-to-cart")
def move_wishlist_item_to_cart(
    wishlist_id: int,
    cart_data: schemas.CartUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    wishlist_item = db.query(models.Wishlist).filter(
        models.Wishlist.id == wishlist_id,
        models.Wishlist.user == current_user["email"]
    ).first()

    if not wishlist_item:
        raise HTTPException(
            status_code=404,
            detail="Wishlist item not found"
        )

    product = db.query(models.Product).filter(
        models.Product.id == wishlist_item.product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    if product.stock < cart_data.quantity:
        raise HTTPException(
            status_code=400,
            detail="Not enough stock available"
        )

    new_cart_item = models.Cart(
        product_id=product.id,
        product_name=product.title,
        quantity=cart_data.quantity,
        price=product.price,
        user_id=current_user["id"]
    )

    # Stock is only decremented at checkout, not during cart add/wishlist move
    db.delete(wishlist_item)
    db.add(new_cart_item)
    db.commit()
    db.refresh(new_cart_item)

    return {
        "message": "Wishlist item moved to cart",
        "cart_item": new_cart_item
    }


@router.delete("/{wishlist_id}")
def remove_from_wishlist(
    wishlist_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    item = db.query(models.Wishlist).filter(
        models.Wishlist.id == wishlist_id,
        models.Wishlist.user == current_user["email"]
    ).first()

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Wishlist item not found"
        )

    db.delete(item)
    db.commit()

    return {
        "message": "Removed from wishlist"
    }