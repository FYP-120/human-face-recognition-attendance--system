from fastapi import APIRouter, HTTPException
from app.models.user import UserModel
from app.core.security import create_access_token

router = APIRouter()

# Dummy Admin (FYP Safe)
ADMIN_EMAIL = "admin@fyp.com"
ADMIN_PASSWORD = "admin123"


@router.post("/login")
def login(user: UserModel):
    if user.email == ADMIN_EMAIL and user.password == ADMIN_PASSWORD:
        token = create_access_token({"sub": user.email})
        return {
            "access_token": token,
            "token_type": "bearer"
        }

    raise HTTPException(status_code=401, detail="Invalid credentials")
