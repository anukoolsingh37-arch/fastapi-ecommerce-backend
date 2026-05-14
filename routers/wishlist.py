from fastapi import APIRouter, Depends
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
    item: schemas.Wishlist,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    new_item = models.Wishlist(
        product_name=item.product_name,
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
        return {
            "message": "Wishlist item not found"
        }

    db.delete(item)
    db.commit()

    return {
        "message": "Removed from wishlist"
    }