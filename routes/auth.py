from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
import hashlib
import logging

router = APIRouter(prefix="/auth", tags=["Auth"])
logger = logging.getLogger("auth")

# In-memory user store
fake_users = {}

class User(BaseModel):
    email: EmailStr
    password: str


@router.post("/signup")
async def signup(user: User):
    """Register a new user"""
    if user.email in fake_users:
        logger.warning(f"❌ Signup failed: {user.email} already exists.")
        raise HTTPException(status_code=400, detail="User already exists.")

    hashed_pw = hashlib.sha256(user.password.encode()).hexdigest()
    fake_users[user.email] = hashed_pw
    logger.info(f"✅ New user created: {user.email}")
    return {"ok": True, "msg": "✅ User created successfully."}


@router.post("/login")
async def login(user: User):
    """Authenticate existing user"""
    hashed_pw = hashlib.sha256(user.password.encode()).hexdigest()
    stored_pw = fake_users.get(user.email)

    if not stored_pw:
        logger.warning(f"❌ Login failed: {user.email} not found.")
        raise HTTPException(status_code=404, detail="User not found.")
    if stored_pw != hashed_pw:
        logger.warning(f"❌ Login failed: invalid password for {user.email}.")
        raise HTTPException(status_code=401, detail="Invalid credentials.")

    logger.info(f"✅ Login successful for {user.email}")
    return {"ok": True, "msg": "✅ Login successful."}
