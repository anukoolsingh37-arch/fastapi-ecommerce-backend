from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from auth.hashing import Hash

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


@router.post("/")
def create_user(user: schemas.UserBase, db: Session = Depends(get_db)):

    # check if email already exists
    existing_user = db.query(models.User).filter(
        models.User.email == user.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
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
def get_users(db: Session = Depends(get_db)):

    users = db.query(models.User).all()

    return users


@router.get("/{id}")
def get_user(id: int, db: Session = Depends(get_db)):

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
def delete_user(id: int, db: Session = Depends(get_db)):

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
    db: Session = Depends(get_db)
):

    user = db.query(models.User).filter(
        models.User.id == id
    )

    if not user.first():
        raise HTTPException(
            status_code=404,
            detail="User not found"
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