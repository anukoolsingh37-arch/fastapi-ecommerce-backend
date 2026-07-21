from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

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


@router.get("/", response_model=list[schemas.UserResponse])
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


@router.get("/{id}", response_model=schemas.UserResponse)
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


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None


@router.put("/{id}")
def update_user(
    id: int,
    updated_user: UserUpdate,
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

    update_data = {}
    if updated_user.username is not None:
        # Check if username is taken
        existing = db.query(models.User).filter(
            models.User.username == updated_user.username,
            models.User.id != id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Username already taken")
        update_data["username"] = updated_user.username
    if updated_user.email is not None:
        existing = db.query(models.User).filter(
            models.User.email == updated_user.email,
            models.User.id != id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
        update_data["email"] = updated_user.email
    if updated_user.password is not None:
        update_data["password"] = Hash.bcrypt(updated_user.password)

    if update_data:
        user.update(update_data)
        db.commit()
        db.refresh(user.first())

        return {
            "message": "User updated successfully",
            "user": {
                "id": id,
                "username": update_data.get("username", current_user.get("username")),
                "email": update_data.get("email", current_user.get("email"))
            }
        }

    return {
        "message": "User updated successfully"
    }
