import os
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable must be set")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def get_current_user(token: str = Depends(oauth2_scheme)):

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        if payload.get("token_type") != "access":
            raise credentials_exception

        email: str = payload.get("sub")
        user_id = payload.get("id")
        username = payload.get("username")
        is_admin = payload.get("is_admin", False)

        if email is None or user_id is None:
            raise credentials_exception

        return {
            "id": user_id,
            "email": email,
            "username": username,
            "is_admin": is_admin
        }

    except JWTError:
        raise credentials_exception