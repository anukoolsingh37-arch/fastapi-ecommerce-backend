from datetime import datetime, date, time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

import models
import schemas

from database import get_db
from auth.oauth2 import get_current_user
from .order_utils import create_order_from_items

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
    return create_order_from_items(
        db=db,
        current_user=current_user,
        items=[item.dict() for item in order.items],
        coupon_code=order.coupon_code
    )


@router.get("/history", response_model=list[schemas.OrderResponse])
def get_order_history(
    status: str = None,
    start_date: date = None,
    end_date: date = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    query = db.query(models.Order).options(
        joinedload(models.Order.items)
    ).filter(
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
        models.OrderItem.product_name,
        func.sum(models.OrderItem.quantity).label("total_quantity"),
        func.sum(models.OrderItem.price * models.OrderItem.quantity).label("total_revenue")
    ).group_by(models.OrderItem.product_name).order_by(
        func.sum(models.OrderItem.quantity).desc()
    ).limit(10).all()

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

    orders = db.query(models.Order).options(
        joinedload(models.Order.items)
    ).order_by(models.Order.created_at.desc()).all()
    return orders


@router.get("/summary")
def order_summary(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    orders = db.query(models.Order).filter(
        models.Order.customer == current_user["email"]
    ).all()

    total_orders = len(orders)
    total_spent = sum(order.total_price for order in orders)

    return {
        "total_orders": total_orders,
        "total_spent": total_spent,
        "orders": orders
    }


@router.get("/{order_id}")
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    order = db.query(models.Order).options(
        joinedload(models.Order.items)
    ).filter(
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
    orders = db.query(models.Order).options(
        joinedload(models.Order.items)
    ).filter(
        models.Order.customer == current_user["email"]
    ).all()

    return orders