# ───────────────────────────────────────────────
# 💰 Finance Router — Brainwash Labs (v2.5.1)
# Stripe + Coinbase checkout integrations (Render-safe)
# ───────────────────────────────────────────────

from fastapi import APIRouter, Request, HTTPException
import stripe
import requests
import os
import json
from pathlib import Path

# ───────────────────────────────────────────────
# 🧩 Router Init
# ───────────────────────────────────────────────
router = APIRouter(
    prefix="/finance",
    tags=["Finance"]
)

# ───────────────────────────────────────────────
# 🔐 Load Environment Variables
# ───────────────────────────────────────────────
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
COINBASE_API_KEY = os.getenv("COINBASE_API_KEY")
COINBASE_API_URL = "https://api.commerce.coinbase.com/charges"

# ───────────────────────────────────────────────
# 💳 Initialize Stripe Safely
# ───────────────────────────────────────────────
if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY

# ───────────────────────────────────────────────
# 📁 Local Data Helpers (optional cache)
# ───────────────────────────────────────────────
DATA_PATH = Path("data/users.json")

def load_users():
    try:
        if DATA_PATH.exists():
            with open(DATA_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        return []
    except Exception:
        return []

def save_users(data):
    try:
        DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[Finance] ⚠️ Failed to save user data: {e}")

# ───────────────────────────────────────────────
# 💳 Stripe Checkout (Create Session)
# ───────────────────────────────────────────────
@router.post("/stripe/checkout")
async def create_stripe_checkout(request: Request):
    """Create a Stripe Checkout session for the given plan."""
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=400, detail="Stripe key not configured in environment")

    try:
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

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url="https://brainwashlabs.com/success",
            cancel_url="https://brainwashlabs.com/cancel",
            customer_email=email,
        )
        return {"url": checkout_session.url}

    except stripe.error.StripeError as e:
        raise HTTPException(status_code=500, detail=f"Stripe error: {e.user_message or str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

# ───────────────────────────────────────────────
# 💰 Coinbase Checkout (Crypto)
# ───────────────────────────────────────────────
@router.post("/coinbase/checkout")
async def create_coinbase_checkout(request: Request):
    """Create a Coinbase Commerce checkout link."""
    if not COINBASE_API_KEY:
        raise HTTPException(status_code=400, detail="Coinbase key not configured in environment")

    try:
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

        response = requests.post(COINBASE_API_URL, headers=headers, json=data)
        if response.status_code != 201:
            raise HTTPException(status_code=400, detail=f"Coinbase API error: {response.text}")

        payload = response.json().get("data", {})
        if not payload:
            raise HTTPException(status_code=400, detail="Coinbase response invalid")

        return {"checkout_url": payload.get("hosted_url")}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

# ───────────────────────────────────────────────
# 🔍 Finance Connection Status
# ───────────────────────────────────────────────
@router.get("/status")
async def finance_status():
    """Health check for finance integrations."""
    stripe_ok = bool(STRIPE_SECRET_KEY)
    coinbase_ok = bool(COINBASE_API_KEY)

    return {
        "finance": "✅ active",
        "stripe_connected": stripe_ok,
        "coinbase_connected": coinbase_ok,
        "stripe_api": "ok" if stripe_ok else "missing",
        "coinbase_api": "ok" if coinbase_ok else "missing",
        "environment": os.getenv("ENV", "production"),
        "version": "v2.5.1"
    }
