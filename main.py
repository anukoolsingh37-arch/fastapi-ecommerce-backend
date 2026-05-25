from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
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
from routers import categories
from routers import shipments
from seed import seed_data
import models

load_dotenv()
models.Base.metadata.create_all(bind=engine)
seed_data()

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
app.include_router(categories.router)
app.include_router(shipments.router)

@app.get("/product", response_class=HTMLResponse)
def product_page():
    with open("static/product.html", "r", encoding="utf-8") as f:
        return f.read()


@app.get("/orders", response_class=HTMLResponse)
def orders_page():
    with open("static/orders.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/admin", response_class=HTMLResponse)
def admin_page():
    with open("static/admin.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/store", response_class=HTMLResponse)
def store():
    with open("static/store.html", "r", encoding="utf-8") as f:
        return f.read()


@app.get("/")
def home():
    return RedirectResponse(url="/store")


