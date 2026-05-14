from datetime import datetime

from pydantic import BaseModel
from typing import List, Optional


class UserBase(BaseModel):
    username: str
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        from_attributes = True


class Product(BaseModel):
    title: str
    description: str
    price: float
    stock: int
    image: str


class ProductResponse(BaseModel):
    id: int
    title: str
    description: str
    price: float
    stock: int
    image: str

    class Config:
        from_attributes = True


class Login(BaseModel):
    username: str
    password: str


class Order(BaseModel):
    product_name: str
    quantity: int
    coupon_code: Optional[str] = None

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: int
    product_name: str
    quantity: int
    total_price: float
    discount_amount: float
    coupon_code: Optional[str]
    customer: str

    class Config:
        from_attributes = True


class InventoryUpdate(BaseModel):
    stock: int


class CouponBase(BaseModel):
    code: str
    description: Optional[str] = None
    discount_percent: float = 0.0
    active: bool = True
    max_uses: Optional[int] = None
    expires_at: Optional[datetime] = None


class CouponResponse(BaseModel):
    id: int
    code: str
    description: Optional[str]
    discount_percent: float
    active: bool
    max_uses: Optional[int]
    used_count: int
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True


class ReviewBase(BaseModel):
    product_id: int
    rating: int
    comment: str


class ReviewResponse(BaseModel):
    id: int
    product_id: int
    user: str
    rating: int
    comment: str
    created_at: datetime

    class Config:
        from_attributes = True


class CartBase(BaseModel):
    product_name: str
    quantity: int
    price: float


class CartDisplay(BaseModel):
    id: int
    product_name: str
    quantity: int
    price: float
    user_id: int

    class Config:
        from_attributes = True

class Wishlist(BaseModel):
    product_name: str


class WishlistResponse(BaseModel):
    id: int
    product_name: str
    user: str

    class Config:
        from_attributes = True