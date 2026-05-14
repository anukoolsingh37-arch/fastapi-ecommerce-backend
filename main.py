from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from database import engine
from routers import products
from routers import user
from routers import login
from routers import orders
from routers import cart
from routers import payment
from routers import wishlist
from routers import coupons
from routers import reviews
import models

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(user.router)
app.include_router(products.router)
app.include_router(login.router)
app.include_router(orders.router)
app.include_router(cart.router)
app.include_router(payment.router)
app.include_router(wishlist.router)
app.include_router(coupons.router)
app.include_router(reviews.router)

@app.get("/store", response_class=HTMLResponse)
def store():
    with open("static/store.html", "r", encoding="utf-8") as f:
        return f.read()


@app.get("/", response_class=HTMLResponse)
def home():
    with open("static/store.html", "r", encoding="utf-8") as f:
        return f.read()


