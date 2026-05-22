from datetime import datetime, date, time

from pydantic import BaseModel
from typing import List, Optional


class UserBase(BaseModel):
    username: str
    email: str
    password: str


class UserProfile(BaseModel):
    id: int
    username: str
    email: str
    is_admin: bool = False

    class Config:
        from_attributes = True


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
    category_id: Optional[int] = None
    featured: bool = False


class ProductUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    image: Optional[str] = None
    category_id: Optional[int] = None
    featured: Optional[bool] = None


class ProductResponse(BaseModel):
    id: int
    title: str
    description: str
    price: float
    stock: int
    image: str
    category_id: Optional[int] = None
    featured: bool = False

    class Config:
        from_attributes = True


class Login(BaseModel):
    username: str
    password: str


class OrderCreate(BaseModel):
    product_id: int
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
    status: str

    class Config:
        from_attributes = True


class OrderStatusUpdate(BaseModel):
    status: str


class ShipmentBase(BaseModel):
    order_id: int
    status: str
    location: Optional[str] = None
    notes: Optional[str] = None


class ShipmentResponse(BaseModel):
    id: int
    order_id: int
    status: str
    location: Optional[str]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class InventoryUpdate(BaseModel):
    stock: int


class CartUpdate(BaseModel):
    quantity: int


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


class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None


class CategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]

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
    product_id: int
    quantity: int


class CartCheckout(BaseModel):
    coupon_code: Optional[str] = None


class CartDisplay(BaseModel):
    id: int
    product_id: int
    product_name: str
    quantity: int
    price: float
    user_id: int

    class Config:
        from_attributes = True


class WishlistItem(BaseModel):
    product_id: int


class WishlistResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    user: str

    class Config:
        from_attributes = True