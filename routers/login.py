from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from auth.hashing import Hash
from auth.jwt_handler import create_access_token, create_refresh_token
from auth.oauth2 import get_current_user

router = APIRouter(
    tags=["Authentication"]
)

@router.post("/login", response_model=schemas.TokenResponse)
def login(
    request: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(
        models.User.username == request.username
    ).first()
    hashed_password = user.password if user else Hash.bcrypt("invalid_password_dummy")

    if not Hash.verify(hashed_password, request.password) or user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={
            "sub": user.email,
            "id": user.id,
            "username": user.username,
            "is_admin": user.is_admin
        }
    )
    refresh_token = create_refresh_token(
        data={
            "sub": user.email,
            "id": user.id,
            "username": user.username,
            "is_admin": user.is_admin
        }
    )

    token_record = models.RefreshToken(
        token=refresh_token,
        user_id=user.id,
        expires_at=datetime.utcnow() + timedelta(days=30)
    )
    db.add(token_record)
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    }


@router.post("/refresh", response_model=schemas.TokenResponse)
def refresh_token(
    refresh_request: schemas.RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    token_record = db.query(models.RefreshToken).filter(
        models.RefreshToken.token == refresh_request.refresh_token,
        models.RefreshToken.revoked == False,
        models.RefreshToken.expires_at >= datetime.utcnow()
    ).first()

    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    user = db.query(models.User).filter(models.User.id == token_record.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    access_token = create_access_token(
        data={
            "sub": user.email,
            "id": user.id,
            "username": user.username,
            "is_admin": user.is_admin
        }
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_request.refresh_token,
        "token_type": "bearer"
    }


@router.post("/logout")
def logout(
    refresh_request: schemas.RefreshTokenRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    token_record = db.query(models.RefreshToken).filter(
        models.RefreshToken.token == refresh_request.refresh_token,
        models.RefreshToken.user_id == current_user["id"]
    ).first()

    if token_record:
        token_record.revoked = True
        db.commit()

    return {"message": "Logged out successfully"}
