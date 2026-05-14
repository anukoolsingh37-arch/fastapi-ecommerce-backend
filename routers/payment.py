from fastapi import APIRouter
from requests import session
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
   
   session = stripe.checkout.Session.create(
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
      "checkout_url": session.url
      }