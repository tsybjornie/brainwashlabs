# ───────────────────────────────────────────────
# 💰 Finance Router — Brainwash Labs (v2.6.0)
# Stripe + Coinbase checkout integrations (Render-safe)
# ───────────────────────────────────────────────

from fastapi import APIRouter, Request, HTTPException
import stripe
import requests
import os
import json
from pathlib import Path
import logging

# ───────────────────────────────────────────────
# 🧩 Router Init (no prefix here; handled by main.py)
# ───────────────────────────────────────────────
router = APIRouter(tags=["Finance"])
logger = logging.getLogger("brainwashlabs.finance")

# ───────────────────────────────────────────────
# 🔐 Environment & External Keys
# ───────────────────────────────────────────────
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
COINBASE_API_KEY = os.getenv("COINBASE_API_KEY")
COINBASE_API_URL = "https://api.commerce.coinbase.com/charges"

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY

# ───────────────────────────────────────────────
# 📁 Local User Cache Helpers
# ───────────────────────────────────────────────
DATA_PATH = Path("data/users.json")

def load_users():
    try:
        if DATA_PATH.exists():
            with open(DATA_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        return []
    except Exception as e:
        logger.warning(f"⚠️ Failed to load users.json: {e}")
        return []

def save_users(data):
    try:
        DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.warning(f"⚠️ Failed to save users.json: {e}")

# ───────────────────────────────────────────────
# 💳 Stripe Checkout — Create Payment Session
# ───────────────────────────────────────────────
@router.post("/stripe/checkout")
async def create_stripe_checkout(request: Request):
    """Create a Stripe Checkout session."""
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=400, detail="Stripe key not configured in environment")

    try:
        body = await request.json()
        email = body.get("email")
        plan = body.get("plan", "monthly")

        if not email:
            raise HTTPException(status_code=400, detail="Email is required")

        price_id = {
            "monthly": "price_XXX_monthly",
            "yearly": "price_XXX_yearly"
        }.get(plan)
        if not price_id:
            raise HTTPException(status_code=400, detail="Invalid plan type")

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url="https://brainwashlabs.com/success",
            cancel_url="https://brainwashlabs.com/cancel",
            customer_email=email,
        )
        logger.info(f"✅ Stripe checkout session created for {email}")
        return {"checkout_url": session.url}

    except stripe.error.StripeError as e:
        msg = e.user_message or str(e)
        logger.error(f"❌ Stripe error: {msg}")
        raise HTTPException(status_code=500, detail=f"Stripe error: {msg}")
    except Exception as e:
        logger.error(f"❌ Internal error during Stripe checkout: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")

# ───────────────────────────────────────────────
# 💰 Coinbase Checkout — Create Crypto Charge
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

        response = requests.post(COINBASE_API_URL, headers=headers, json=data, timeout=10)
        if response.status_code != 201:
            logger.error(f"❌ Coinbase API error: {response.text}")
            raise HTTPException(status_code=400, detail=f"Coinbase API error: {response.text}")

        payload = response.json().get("data", {})
        if not payload:
            raise HTTPException(status_code=400, detail="Coinbase returned empty payload")

        logger.info(f"✅ Coinbase checkout created for {email}")
        return {"checkout_url": payload.get("hosted_url")}

    except requests.exceptions.RequestException as e:
        logger.error(f"⚠️ Coinbase network error: {e}")
        raise HTTPException(status_code=502, detail=f"Coinbase network error: {e}")
    except Exception as e:
        logger.error(f"❌ Internal error during Coinbase checkout: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")

# ───────────────────────────────────────────────
# 🔍 Finance Connection Status
# ───────────────────────────────────────────────
@router.get("/status")
async def finance_status():
    """Health check for finance integrations (Stripe + Coinbase)."""
    stripe_ok = bool(STRIPE_SECRET_KEY)
    coinbase_ok = bool(COINBASE_API_KEY)

    # Lightweight ping to Coinbase (optional)
    coinbase_live = False
    try:
        if coinbase_ok:
            ping = requests.get(
                "https://api.commerce.coinbase.com/checkouts",
                headers={
                    "X-CC-Api-Key": COINBASE_API_KEY,
                    "X-CC-Version": "2018-03-22"
                },
                timeout=5
            )
            coinbase_live = ping.status_code in (200, 201)
    except Exception:
        coinbase_live = False

    return {
        "finance": "✅ active",
        "stripe_connected": stripe_ok,
        "coinbase_connected": coinbase_ok,
        "coinbase_live": coinbase_live,
        "stripe_api": "ok" if stripe_ok else "missing",
        "coinbase_api": "ok" if coinbase_ok else "missing",
        "environment": os.getenv("ENV", "production"),
        "version": "v2.6.0"
    }
