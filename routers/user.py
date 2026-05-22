from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from auth.hashing import Hash
from auth.oauth2 import get_current_user

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


def require_admin(current_user: dict):
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )


@router.post("/")
def create_user(user: schemas.UserBase, db: Session = Depends(get_db)):

    # check if email already exists
    existing_email = db.query(models.User).filter(
        models.User.email == user.email
    ).first()

    if existing_email:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    existing_username = db.query(models.User).filter(
        models.User.username == user.username
    ).first()

    if existing_username:
        raise HTTPException(
            status_code=400,
            detail="Username already taken"
        )

    hashed_password = Hash.bcrypt(user.password)

    # create new user
    new_user = models.User(
        username=user.username,
        email=user.email,
        password=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User created successfully",
        "user": {
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email
        }
    }


@router.get("/")
def get_users(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    require_admin(current_user)

    users = db.query(models.User).all()

    return users


@router.get("/me", response_model=schemas.UserProfile)
def get_me(current_user: dict = Depends(get_current_user)):
    return current_user


@router.get("/{id}")
def get_user(
    id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["id"] != id and not current_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted"
        )

    user = db.query(models.User).filter(
        models.User.id == id
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return user


@router.delete("/{id}")
def delete_user(
    id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    if current_user["id"] != id and not current_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted"
        )

    user = db.query(models.User).filter(
        models.User.id == id
    )

    if not user.first():
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    user.delete(synchronize_session=False)
    db.commit()

    return {
        "message": "User deleted successfully"
    }


@router.put("/{id}")
def update_user(
    id: int,
    updated_user: schemas.UserBase,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    user = db.query(models.User).filter(
        models.User.id == id
    )

    if not user.first():
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if current_user["id"] != id and not current_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted"
        )

    hashed_password = Hash.bcrypt(updated_user.password)

    user.update({
        "username": updated_user.username,
        "email": updated_user.email,
        "password": hashed_password
    })

    db.commit()

    return {
        "message": "User updated successfully"
    }