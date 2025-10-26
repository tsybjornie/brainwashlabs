from fastapi import APIRouter, Request, HTTPException
import stripe
import requests
import os
import json
from pathlib import Path

router = APIRouter(prefix="/api/finance", tags=["Finance"])

# ───────────────────────────────────────────────
# 🔐 Load environment variables
# ───────────────────────────────────────────────
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
COINBASE_API_KEY = os.getenv("COINBASE_API_KEY")
COINBASE_API_URL = "https://api.commerce.coinbase.com/charges"

# ───────────────────────────────────────────────
# 💳 Initialize Stripe safely
# ───────────────────────────────────────────────
if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY

DATA_PATH = Path("data/users.json")

def load_users():
    if not DATA_PATH.exists():
        return []
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(data):
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# ───────────────────────────────────────────────
# 💳 Stripe Checkout (create session)
# ───────────────────────────────────────────────
@router.post("/stripe/checkout")
async def create_stripe_checkout(request: Request):
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=400, detail="Stripe key not configured in environment")

    body = await request.json()
    email = body.get("email")
    plan = body.get("plan", "monthly")

    if not email:
        raise HTTPException(status_code=400, detail="Email required")

    price_id = {
        "monthly": "price_XXX_monthly",
        "yearly": "price_XXX_yearly"
    }.get(plan)

    if not price_id:
        raise HTTPException(status_code=400, detail="Invalid plan type")

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url="https://brainwashlabs.com/success",
            cancel_url="https://brainwashlabs.com/cancel",
            customer_email=email,
        )
        return {"url": checkout_session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ───────────────────────────────────────────────
# 💰 Coinbase Checkout (crypto)
# ───────────────────────────────────────────────
@router.post("/coinbase/checkout")
async def create_coinbase_checkout(request: Request):
    if not COINBASE_API_KEY:
        raise HTTPException(status_code=400, detail="Coinbase key not configured in environment")

    body = await request.json()
    email = body.get("email")
    plan = body.get("plan", "monthly")

    if not email:
        raise HTTPException(status_code=400, detail="Email required")

    headers = {
        "X-CC-Api-Key": COINBASE_API_KEY,
        "X-CC-Version": "2018-03-22",
        "Content-Type": "application/json"
    }

    data = {
        "name": f"Brainwash Labs Subscription ({plan})",
        "description": "AI SaaS Subscription",
        "pricing_type": "fixed_price",
        "local_price": {
            "amount": "59.00" if plan == "monthly" else "590.00",
            "currency": "USD"
        },
        "metadata": {"email": email, "plan": plan},
        "redirect_url": "https://brainwashlabs.com/success",
        "cancel_url": "https://brainwashlabs.com/cancel"
    }

    try:
        response = requests.post(COINBASE_API_URL, headers=headers, json=data)
        if response.status_code != 201:
            raise HTTPException(status_code=400, detail=response.text)
        charge = response.json()["data"]
        return {"checkout_url": charge["hosted_url"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ───────────────────────────────────────────────
# 🧩 Health check
# ───────────────────────────────────────────────
@router.get("/status")
async def finance_status():
    return {
        "stripe_connected": bool(STRIPE_SECRET_KEY),
        "coinbase_connected": bool(COINBASE_API_KEY)
    }
# ───────────────────────────────────────────────
# 🔍 Finance Connection Status
# ───────────────────────────────────────────────
@router.get("/status")
async def finance_status():
    return {
        "stripe_connected": bool(STRIPE_SECRET_KEY),
        "coinbase_connected": bool(COINBASE_API_KEY),
        "environment": os.getenv("ENV", "production")
    }
