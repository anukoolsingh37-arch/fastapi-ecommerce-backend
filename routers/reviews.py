from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas

from database import get_db
from auth.oauth2 import get_current_user

router = APIRouter(
    prefix="/reviews",
    tags=["Reviews"]
)


@router.post("/", response_model=schemas.ReviewResponse)
def create_review(
    review: schemas.ReviewBase,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    product = db.query(models.Product).filter(
        models.Product.id == review.product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    if review.rating < 1 or review.rating > 5:
        raise HTTPException(
            status_code=400,
            detail="Rating must be between 1 and 5"
        )

    new_review = models.Review(
        product_id=review.product_id,
        user=current_user["email"],
        rating=review.rating,
        comment=review.comment
    )

    db.add(new_review)
    db.commit()
    db.refresh(new_review)

    return new_review


@router.get("/product/{product_id}", response_model=list[schemas.ReviewResponse])
def get_product_reviews(
    product_id: int,
    db: Session = Depends(get_db)
):
    return db.query(models.Review).filter(
        models.Review.product_id == product_id
    ).all()


@router.get("/")
def list_reviews(
    db: Session = Depends(get_db)
):
    return db.query(models.Review).all()


@router.get("/user")
def get_user_reviews(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return db.query(models.Review).filter(
        models.Review.user == current_user["email"]
    ).all()
