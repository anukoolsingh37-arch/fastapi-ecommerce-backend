from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas

from database import get_db
from auth.oauth2 import get_current_user

router = APIRouter(
    prefix="/coupons",
    tags=["Coupons"]
)


@router.post("/", response_model=schemas.CouponResponse)
def create_coupon(
    coupon: schemas.CouponBase,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )
    existing = db.query(models.Coupon).filter(
        models.Coupon.code == coupon.code
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Coupon code already exists"
        )

    new_coupon = models.Coupon(
        code=coupon.code,
        description=coupon.description,
        discount_percent=coupon.discount_percent,
        active=coupon.active,
        max_uses=coupon.max_uses or 0,
        expires_at=coupon.expires_at
    )

    db.add(new_coupon)
    db.commit()
    db.refresh(new_coupon)

    return new_coupon


@router.get("/", response_model=list[schemas.CouponResponse])
def list_coupons(
    db: Session = Depends(get_db)
):
    return db.query(models.Coupon).all()


@router.get("/validate")
def validate_coupon(
    code: str,
    db: Session = Depends(get_db)
):
    coupon = db.query(models.Coupon).filter(
        models.Coupon.code == code,
        models.Coupon.active == True
    ).first()

    if not coupon:
        raise HTTPException(
            status_code=404,
            detail="Coupon not found or inactive"
        )

    return {
        "code": coupon.code,
        "discount_percent": coupon.discount_percent,
        "active": coupon.active,
        "max_uses": coupon.max_uses,
        "used_count": coupon.used_count,
        "expires_at": coupon.expires_at
    }


@router.get("/{coupon_id}", response_model=schemas.CouponResponse)
def get_coupon(
    coupon_id: int,
    db: Session = Depends(get_db)
):
    coupon = db.query(models.Coupon).filter(
        models.Coupon.id == coupon_id
    ).first()

    if not coupon:
        raise HTTPException(
            status_code=404,
            detail="Coupon not found"
        )

    return coupon


@router.put("/{coupon_id}", response_model=schemas.CouponResponse)
def update_coupon(
    coupon_id: int,
    coupon_data: schemas.CouponBase,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )
    coupon = db.query(models.Coupon).filter(
        models.Coupon.id == coupon_id
    ).first()

    if not coupon:
        raise HTTPException(
            status_code=404,
            detail="Coupon not found"
        )

    coupon.code = coupon_data.code
    coupon.description = coupon_data.description
    coupon.discount_percent = coupon_data.discount_percent
    coupon.active = coupon_data.active
    coupon.max_uses = coupon_data.max_uses or 0
    coupon.expires_at = coupon_data.expires_at

    db.commit()
    db.refresh(coupon)

    return coupon


@router.delete("/{coupon_id}")
def delete_coupon(
    coupon_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )
    coupon = db.query(models.Coupon).filter(
        models.Coupon.id == coupon_id
    ).first()

    if not coupon:
        raise HTTPException(
            status_code=404,
            detail="Coupon not found"
        )

    db.delete(coupon)
    db.commit()

    return {"message": "Coupon deleted successfully"}
