from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

import models


def validate_coupon(db: Session, coupon_code: str):
    coupon = db.query(models.Coupon).filter(
        models.Coupon.code == coupon_code,
        models.Coupon.active == True
    ).first()

    if not coupon:
        raise HTTPException(
            status_code=400,
            detail="Invalid coupon code"
        )

    if coupon.expires_at and coupon.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=400,
            detail="Coupon has expired"
        )

    if coupon.max_uses and coupon.used_count >= coupon.max_uses:
        raise HTTPException(
            status_code=400,
            detail="Coupon usage limit reached"
        )

    return coupon


def create_order_from_items(
    db: Session,
    current_user: dict,
    items: list[dict],
    coupon_code: str | None = None,
    cart_items: list[models.Cart] | None = None
):
    if not items:
        raise HTTPException(
            status_code=400,
            detail="Order must have at least one item"
        )

    total_price = 0.0
    order_items = []

    for item in items:
        product = db.query(models.Product).filter(
            models.Product.id == item["product_id"]
        ).first()

        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Product with id {item['product_id']} not found"
            )

        if item["quantity"] < 1:
            raise HTTPException(
                status_code=400,
                detail="Quantity must be at least 1"
            )

        if product.stock < item["quantity"]:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough stock for {product.title}. Available: {product.stock}"
            )

        line_total = product.price * item["quantity"]
        total_price += line_total
        order_items.append({
            "product_id": product.id,
            "product_name": product.title,
            "quantity": item["quantity"],
            "price": product.price
        })

    discount_amount = 0.0
    coupon = None
    if coupon_code:
        coupon = validate_coupon(db, coupon_code)
        discount_amount = total_price * (coupon.discount_percent / 100)
        total_price = max(total_price - discount_amount, 0.0)
        coupon.used_count += 1

    new_order = models.Order(
        total_price=total_price,
        discount_amount=discount_amount,
        coupon_code=coupon_code,
        customer=current_user["email"],
        customer_id=current_user["id"],
        status="pending"
    )

    db.add(new_order)
    db.flush()

    for item in items:
        updated_rows = db.query(models.Product).filter(
            models.Product.id == item["product_id"],
            models.Product.stock >= item["quantity"]
        ).update(
            {models.Product.stock: models.Product.stock - item["quantity"]},
            synchronize_session=False
        )

        if updated_rows != 1:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for product id {item['product_id']}"
            )

    for item_data in order_items:
        order_item = models.OrderItem(
            order_id=new_order.id,
            product_id=item_data["product_id"],
            product_name=item_data["product_name"],
            quantity=item_data["quantity"],
            price=item_data["price"]
        )
        db.add(order_item)

    if cart_items:
        for cart_item in cart_items:
            db.delete(cart_item)

    db.commit()
    db.refresh(new_order)

    return db.query(models.Order).options(
        joinedload(models.Order.items)
    ).filter(models.Order.id == new_order.id).first()
