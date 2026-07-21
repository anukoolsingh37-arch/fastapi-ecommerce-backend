from fastapi import APIRouter, Depends, HTTPException
from dotenv import load_dotenv
import os
import stripe
from sqlalchemy.orm import Session

import models
from database import get_db
from auth.oauth2 import get_current_user

load_dotenv()

router = APIRouter(
    prefix="/payment",
    tags=["Payment"]
)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


@router.post("/checkout")
def create_checkout_session(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not stripe.api_key:
        raise HTTPException(
            status_code=500,
            detail="Stripe secret key is not configured"
        )

    cart_items = db.query(models.Cart).filter(models.Cart.user_id == current_user["id"]).all()
    if not cart_items:
        raise HTTPException(
            status_code=400,
            detail="Cart is empty"
        )

    line_items = []
    for item in cart_items:
        product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if not product or product.stock < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for {item.product_name}"
            )
        line_items.append({
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': product.title,
                },
                'unit_amount': int(round(product.price * 100)),
            },
            'quantity': item.quantity,
        })

    success_url = os.getenv("STRIPE_SUCCESS_URL", "http://localhost:3000/success")
    cancel_url = os.getenv("STRIPE_CANCEL_URL", "http://localhost:3000/cancel")

    checkout_session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=line_items,
        mode="payment",
        success_url=success_url,
        cancel_url=cancel_url
    )
    return {
        "checkout_url": checkout_session.url
    }
