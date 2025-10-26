# routes/auth.py
# 🧠 Brainwash Labs — Auth Router (Render-Proof Edition)

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
import hashlib
import logging
from typing import Dict

# ───────────────────────────────────────────────
# 🚀 Router Setup
# ───────────────────────────────────────────────
router = APIRouter(prefix="/auth", tags=["Auth"])
logger = logging.getLogger("auth")

# ───────────────────────────────────────────────
# 🧩 Temporary In-Memory Store (demo only)
# ───────────────────────────────────────────────
# You’ll eventually replace this with a real database.
fake_users: Dict[str, str] = {}

# ───────────────────────────────────────────────
# 🧱 Data Model
# ───────────────────────────────────────────────
class User(BaseModel):
    email: EmailStr
    password: str

# ───────────────────────────────────────────────
# ✳️ Utility Function (hashing)
# ───────────────────────────────────────────────
def hash_password(password: str) -> str:
    """Return SHA-256 hash of password."""
    return hashlib.sha256(password.encode()).hexdigest()

# ───────────────────────────────────────────────
# 🧾 Signup Endpoint
# ───────────────────────────────────────────────
@router.post("/signup")
async def signup(user: User):
    """Register a new user (in-memory demo)."""
    if user.email in fake_users:
        logger.warning(f"❌ Signup failed — {user.email} already exists.")
        raise HTTPException(status_code=400, detail="User already exists.")

    fake_users[user.email] = hash_password(user.password)
    logger.info(f"✅ New user created: {user.email}")
    return {"ok": True, "msg": "User created successfully."}

# ───────────────────────────────────────────────
# 🔐 Login Endpoint
# ───────────────────────────────────────────────
@router.post("/login")
async def login(user: User):
    """Authenticate an existing user."""
    stored_pw = fake_users.get(user.email)

    if not stored_pw:
        logger.warning(f"❌ Login failed — {user.email} not found.")
        raise HTTPException(status_code=404, detail="User not found.")

    if stored_pw != hash_password(user.password):
        logger.warning(f"❌ Login failed — invalid password for {user.email}.")
        raise HTTPException(status_code=401, detail="Invalid credentials.")

    logger.info(f"✅ Login successful for {user.email}")
    return {"ok": True, "msg": "Login successful."}

# ───────────────────────────────────────────────
# 🧠 Status Endpoint (Router Verification)
# ───────────────────────────────────────────────
@router.get("/status")
async def auth_status():
    """Simple router health and user count check."""
    logger.info("🧩 /auth/status triggered")
    return {
        "ok": True,
        "msg": "✅ Auth service online.",
        "users_registered": len(fake_users),
        "env": "production"
    }
