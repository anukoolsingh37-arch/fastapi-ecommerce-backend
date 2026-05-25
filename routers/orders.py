from datetime import datetime, date, time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

import models
import schemas

from database import get_db
from auth.oauth2 import get_current_user

router = APIRouter(
    prefix="/orders",
    tags=["Orders"]
)


@router.post("/", response_model=schemas.OrderResponse)
def create_order(
    order: schemas.OrderCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    product = db.query(models.Product).filter(
        models.Product.id == order.product_id
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
        product_id=product.id,
        product_name=product.title,
        quantity=order.quantity,
        total_price=total_price,
        discount_amount=discount_amount,
        coupon_code=order.coupon_code,
        customer=current_user["email"],
        status="pending"
    )

    product.stock -= order.quantity

    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    return new_order


@router.get("/history", response_model=list[schemas.OrderResponse])
def get_order_history(
    status: str = None,
    start_date: date = None,
    end_date: date = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    query = db.query(models.Order).filter(
        models.Order.customer == current_user["email"]
    )

    if status:
        query = query.filter(models.Order.status == status)

    if start_date:
        start_dt = datetime.combine(start_date, time.min)
        query = query.filter(models.Order.created_at >= start_dt)

    if end_date:
        end_dt = datetime.combine(end_date, time.max)
        query = query.filter(models.Order.created_at <= end_dt)

    return query.order_by(models.Order.created_at.desc()).all()


@router.get("/admin/sales-summary")
def get_sales_summary(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )

    total_orders = db.query(models.Order).count()
    total_revenue = db.query(models.Order).with_entities(
        func.coalesce(func.sum(models.Order.total_price), 0.0)
    ).scalar() or 0.0

    best_sellers = db.query(
        models.Order.product_name,
        func.sum(models.Order.quantity).label("total_quantity"),
        func.sum(models.Order.total_price).label("total_revenue")
    ).group_by(models.Order.product_name).order_by(func.sum(models.Order.quantity).desc()).limit(10).all()

    best_sellers_data = [
        {
            "product_name": result.product_name,
            "total_quantity": int(result.total_quantity),
            "total_revenue": float(result.total_revenue)
        }
        for result in best_sellers
    ]

    return {
        "total_orders": total_orders,
        "total_revenue": float(total_revenue),
        "best_sellers": best_sellers_data
    }


@router.get("/admin/orders")
def get_admin_orders(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )

    orders = db.query(models.Order).order_by(models.Order.created_at.desc()).all()
    return orders


@router.get("/{order_id}")
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    order = db.query(models.Order).filter(
        models.Order.id == order_id
    ).first()

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    if order.customer != current_user["email"] and not current_user.get("is_admin"):
        raise HTTPException(
            status_code=403,
            detail="Operation not permitted"
        )

    return order


@router.patch("/{order_id}/status")
def update_order_status(
    order_id: int,
    status_update: schemas.OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )

    order = db.query(models.Order).filter(
        models.Order.id == order_id
    ).first()

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    order.status = status_update.status
    db.commit()
    db.refresh(order)

    return {
        "message": "Order status updated",
        "order": order
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