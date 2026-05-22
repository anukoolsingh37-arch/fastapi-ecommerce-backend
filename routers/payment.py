from fastapi import APIRouter, HTTPException
from dotenv import load_dotenv
import os
import stripe

load_dotenv()

router = APIRouter(
    prefix="/payment",
    tags=["Payment"]

)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

@router.post("/checkout")
def create_checkout_session():
    if not stripe.api_key:
        raise HTTPException(
            status_code=500,
            detail="Stripe secret key is not configured"
        )

    checkout_session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': 'T-shirt',
                },
                'unit_amount': 2000,
            },
            'quantity': 1,
        }],
        mode="payment",
        success_url="http://localhost:3000/success",
        cancel_url="http://localhost:3000/cancel"
    )
    return {
        "checkout_url": checkout_session.url
    }