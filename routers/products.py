from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import or_, func, desc
from sqlalchemy.orm import Session, joinedload
import os
import shutil
import uuid

from database import get_db
from auth.oauth2 import get_current_user

import models
import schemas

router = APIRouter(
    tags=["Products"]
)

UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/products")
def create_product(
    product: schemas.Product,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )

    new_product = models.Product(
        title=product.title,
        description=product.description,
        price=product.price,
        stock=product.stock,
        image=product.image,
        category_id=product.category_id,
        featured=product.featured
    )

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return {
        "message": "Product created successfully",
        "product": new_product
    }


@router.get("/products")
def get_products(
    page: int = 1,
    limit: int = 5,
    db: Session = Depends(get_db)
):

    skip = (page - 1) * limit

    products = db.query(models.Product).offset(skip).limit(limit).all()

    return {
        "page": page,
        "limit": limit,
        "products": products
    }


@router.get("/products/featured")
def get_featured_products(
    db: Session = Depends(get_db)
):
    products = db.query(models.Product).filter(
        models.Product.featured == True
    ).all()
    return products


@router.get("/products/low-stock")
def get_low_stock_products(
    threshold: int = 5,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )

    products = db.query(models.Product).filter(
        models.Product.stock <= threshold
    ).order_by(models.Product.stock.asc()).all()

    return {
        "threshold": threshold,
        "low_stock_products": products
    }


@router.get("/products/search")
def search_products(
    search: str = None,
    category_id: int = None,
    min_price: float = None,
    max_price: float = None,
    in_stock: bool = None,
    sort_by: str = None,
    db: Session = Depends(get_db)
):

    query = db.query(models.Product)

    if search:
        query = query.filter(
            or_(
                models.Product.title.ilike(f"%{search}%"),
                models.Product.description.ilike(f"%{search}%")
            )
        )

    if category_id is not None:
        query = query.filter(
            models.Product.category_id == category_id
        )

    if in_stock is not None:
        if in_stock:
            query = query.filter(models.Product.stock > 0)
        else:
            query = query.filter(models.Product.stock == 0)

    if min_price is not None:
        query = query.filter(
            models.Product.price >= min_price
        )

    if max_price is not None:
        query = query.filter(
            models.Product.price <= max_price
        )

    if sort_by == "low":
        query = query.order_by(
            models.Product.price.asc()
        )

    elif sort_by == "high":
        query = query.order_by(
            models.Product.price.desc()
        )

    products = query.all()

    return products


@router.get("/products/top-rated")
def get_top_rated_products(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    results = db.query(
        models.Product,
        func.coalesce(func.avg(models.Review.rating), 0).label("average_rating"),
        func.count(models.Review.id).label("review_count")
    ).outerjoin(models.Review)
    query = results.group_by(models.Product.id).order_by(desc("average_rating"), desc("review_count")).limit(limit)

    top_products = []
    for product, average_rating, review_count in query:
        top_products.append({
            "product": product,
            "average_rating": float(round(average_rating or 0, 2)),
            "review_count": review_count
        })

    return top_products


@router.get("/products/{product_id}/recommendations")
def get_product_recommendations(
    product_id: int,
    limit: int = 8,
    db: Session = Depends(get_db)
):
    product = db.query(models.Product).filter(
        models.Product.id == product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    query = db.query(
        models.Product,
        func.coalesce(func.avg(models.Review.rating), 0).label("average_rating"),
        func.count(models.Review.id).label("review_count")
    ).outerjoin(models.Review).filter(
        models.Product.id != product_id,
        models.Product.category_id == product.category_id
    ).group_by(models.Product.id)

    recommendations = query.order_by(desc("average_rating"), desc("review_count"), desc(models.Product.featured)).limit(limit).all()

    if not recommendations:
        fallback = db.query(
            models.Product,
            func.coalesce(func.avg(models.Review.rating), 0).label("average_rating"),
            func.count(models.Review.id).label("review_count")
        ).outerjoin(models.Review).group_by(models.Product.id).order_by(desc("average_rating"), desc("review_count"), desc(models.Product.featured)).limit(limit).all()
        recommendations = fallback

    result = []
    for recommended, average_rating, review_count in recommendations:
        result.append({
            "product": recommended,
            "average_rating": float(round(average_rating or 0, 2)),
            "review_count": review_count
        })

    return result


@router.get("/products/{product_id}")
def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):

    product = db.query(models.Product).filter(
        models.Product.id == product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    return product


@router.get("/products/{product_id}/review-summary")
def get_product_review_summary(
    product_id: int,
    db: Session = Depends(get_db)
):
    product = db.query(models.Product).filter(
        models.Product.id == product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    average_rating = db.query(func.avg(models.Review.rating)).filter(
        models.Review.product_id == product_id
    ).scalar() or 0.0

    review_count = db.query(func.count(models.Review.id)).filter(
        models.Review.product_id == product_id
    ).scalar()

    return {
        "product_id": product_id,
        "average_rating": round(float(average_rating), 2),
        "review_count": review_count,
        "product_name": product.title
    }


@router.put("/products/{product_id}")
def update_product(
    product_id: int,
    product: schemas.ProductUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )

    existing_product = db.query(models.Product).filter(
        models.Product.id == product_id
    ).first()

    if not existing_product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    if product.title is not None:
        existing_product.title = product.title
    if product.description is not None:
        existing_product.description = product.description
    if product.price is not None:
        existing_product.price = product.price
    if product.stock is not None:
        existing_product.stock = product.stock
    if product.image is not None:
        existing_product.image = product.image
    if product.category_id is not None:
        existing_product.category_id = product.category_id
    if product.featured is not None:
        existing_product.featured = product.featured

    db.commit()

    return {
        "message": "Product updated successfully"
    }


@router.delete("/products/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )

    existing_product = db.query(models.Product).filter(
        models.Product.id == product_id
    ).first()

    if not existing_product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    db.delete(existing_product)
    db.commit()

    return {
        "message": "Product deleted successfully"
    }


@router.get("/products/{product_id}/stock")
def get_product_stock(
    product_id: int,
    db: Session = Depends(get_db)
):
    product = db.query(models.Product).filter(
        models.Product.id == product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    return {
        "product_id": product.id,
        "stock": product.stock
    }


@router.patch("/products/{product_id}/stock")
def update_product_stock(
    product_id: int,
    inventory: schemas.InventoryUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )

    product = db.query(models.Product).filter(
        models.Product.id == product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    product.stock = inventory.stock
    db.commit()

    return {
        "message": "Product stock updated successfully",
        "product_id": product.id,
        "stock": product.stock
    }


@router.post("/upload")
def upload_image(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )

    allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    max_upload_size = int(os.getenv("MAX_UPLOAD_SIZE", 5 * 1024 * 1024))

    ext = os.path.splitext(file.filename)[1].lower() if file.filename else ""
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Allowed types: jpg, jpeg, png, gif, webp"
        )

    contents = file.file.read()
    if len(contents) > max_upload_size:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds the maximum allowed size of {max_upload_size} bytes"
        )

    filename = f"{uuid.uuid4().hex}{ext or '.jpg'}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    with open(filepath, "wb") as buffer:
        buffer.write(contents)

    return {
        "message": "Image uploaded successfully",
        "url": f"/static/uploads/{filename}"
    }
