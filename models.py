from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.sql import func
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    email = Column(String, unique=True)
    password = Column(String)


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    price = Column(Float)
    stock = Column(Integer, default=0)
    image = Column(String)


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String)
    quantity = Column(Integer)
    total_price = Column(Float)
    discount_amount = Column(Float, default=0.0)
    coupon_code = Column(String, nullable=True)
    customer = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Coupon(Base):
    __tablename__ = "coupons"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)
    description = Column(String, nullable=True)
    discount_percent = Column(Float, default=0.0)
    active = Column(Boolean, default=True)
    max_uses = Column(Integer, default=0)
    used_count = Column(Integer, default=0)
    expires_at = Column(DateTime, nullable=True)


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    user = Column(String)
    rating = Column(Integer)
    comment = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Cart(Base):
    __tablename__ = "cart"

    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String)
    quantity = Column(Integer)
    price = Column(Float)
    user_id = Column(Integer, ForeignKey("users.id"))

class Wishlist(Base):
    __tablename__ = "wishlist"

    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String)
    user = Column(String)