from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

import models
from database import get_db
from auth.hashing import Hash
from auth.jwt_handler import create_access_token

router = APIRouter(
    tags=["Authentication"]
)


@router.post("/login")
def login(
    request: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):

    user = db.query(models.User).filter(
        models.User.username == request.username
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Invalid username"
        )

    if not Hash.verify(user.password, request.password):
        raise HTTPException(
            status_code=401,
            detail="Invalid password"
        )

    access_token = create_access_token(
        data={
            "sub": user.email,
            "id": user.id,
            "username": user.username
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    }