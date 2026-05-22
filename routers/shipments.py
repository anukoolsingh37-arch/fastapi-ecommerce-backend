import os
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from auth.oauth2 import get_current_user

load_dotenv()

router = APIRouter(
    prefix="/shipments",
    tags=["Shipments"]
)


SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
EMAIL_FROM = os.getenv("EMAIL_FROM")


def send_shipment_email(to_email: str, subject: str, body: str):
    if not (SMTP_HOST and SMTP_USER and SMTP_PASSWORD and EMAIL_FROM):
        return

    message = EmailMessage()
    message["From"] = EMAIL_FROM
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(SMTP_USER, SMTP_PASSWORD)
        smtp.send_message(message)


def require_admin(current_user: dict):
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )


@router.post("/", response_model=schemas.ShipmentResponse)
def create_shipment(
    shipment: schemas.ShipmentBase,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    require_admin(current_user)

    order = db.query(models.Order).filter(
        models.Order.id == shipment.order_id
    ).first()

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    new_shipment = models.Shipment(
        order_id=shipment.order_id,
        status=shipment.status,
        location=shipment.location,
        notes=shipment.notes
    )
    db.add(new_shipment)

    order.status = shipment.status
    db.commit()
    db.refresh(new_shipment)

    if order.customer:
        subject = f"Shipment update for order #{order.id}"
        body = (
            f"Hello,\n\nYour order #{order.id} has a new shipment update:\n"
            f"Status: {shipment.status}\n"
            f"Location: {shipment.location or 'N/A'}\n"
            f"Notes: {shipment.notes or 'No additional notes.'}\n\n"
            "Thank you for shopping with us."
        )
        send_shipment_email(order.customer, subject, body)

    return new_shipment


@router.get("/order/{order_id}", response_model=list[schemas.ShipmentResponse])
def get_order_shipments(
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

    return db.query(models.Shipment).filter(
        models.Shipment.order_id == order_id
    ).order_by(models.Shipment.created_at).all()


@router.get("/")
def list_shipments(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    require_admin(current_user)
    return db.query(models.Shipment).order_by(models.Shipment.created_at.desc()).all()
