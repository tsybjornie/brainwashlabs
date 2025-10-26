from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
import hashlib
import logging
import os

# ───────────────────────────────────────────────
# 🧩 Router Config
# ───────────────────────────────────────────────
router = APIRouter(prefix="/auth", tags=["Auth"])
logger = logging.getLogger("auth")

# Simple in-memory store (replace with DB later)
fake_users = {}

# ───────────────────────────────────────────────
# 🧱 Data Models
# ───────────────────────────────────────────────
class User(BaseModel):
    email: EmailStr
    password: str


# ───────────────────────────────────────────────
# 🧠 Utility — Hash password safely
# ───────────────────────────────────────────────
def hash_password(password: str) -> str:
    salt = os.getenv("AUTH_SALT", "brainwashlabs")  # add simple salt
    return hashlib.sha256((password + salt).encode()).hexdigest()


# ───────────────────────────────────────────────
# 🚀 Signup Route
# ───────────────────────────────────────────────
@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(user: User):
    """Register a new user (simple demo version)"""
    if user.email in fake_users:
        logger.warning(f"❌ Signup failed: {user.email} already exists.")
        raise HTTPException(status_code=400, detail="User already exists.")

    fake_users[user.email] = hash_password(user.password)
    logger.info(f"✅ New user created: {user.email}")
    return {
        "ok": True,
        "msg": "✅ User created successfully.",
        "email": user.email
    }


# ───────────────────────────────────────────────
# 🔑 Login Route
# ───────────────────────────────────────────────
@router.post("/login", status_code=status.HTTP_200_OK)
async def login(user: User):
    """Authenticate existing user"""
    stored_pw = fake_users.get(user.email)
    if not stored_pw:
        logger.warning(f"❌ Login failed: {user.email} not found.")
        raise HTTPException(status_code=404, detail="User not found.")

    if stored_pw != hash_password(user.password):
        logger.warning(f"❌ Login failed: invalid password for {user.email}.")
        raise HTTPException(status_code=401, detail="Invalid credentials.")

    logger.info(f"✅ Login successful for {user.email}")
    return {
        "ok": True,
        "msg": "✅ Login successful.",
        "email": user.email
    }


# ───────────────────────────────────────────────
# 🧹 Health / Debug Route
# ───────────────────────────────────────────────
@router.get("/status")
async def auth_status():
    """Quick check if auth router is alive"""
    return {
        "ok": True,
        "users_registered": len(fake_users),
        "env": os.getenv("ENV", "production")
    }
