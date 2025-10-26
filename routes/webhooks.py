# ───────────────────────────────────────────────
# 🔔 Webhooks Router — Brainwash Labs
# Stripe & Coinbase post-payment verification
# ───────────────────────────────────────────────

from fastapi import APIRouter, Request, HTTPException
import stripe
import json
import hmac
import hashlib
import os
import requests

router = APIRouter(prefix="/api/webhooks", tags=["Webhooks"])

# ───────────────────────────────────────────────
# ⚙️ Stripe Webhook
# ───────────────────────────────────────────────
@router.post("/stripe")
async def stripe_webhook(request: Request):
    """Stripe webhook handler for completed payments."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

    if not webhook_secret:
        raise HTTPException(status_code=400, detail="Stripe webhook secret missing")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_type = event.get("type")
    data = event.get("data", {}).get("object", {})

    if event_type in ["checkout.session.completed", "invoice.paid", "payment_intent.succeeded"]:
        email = data.get("customer_email") or data.get("receipt_email")
        amount = data.get("amount_total", 0) / 100
        print(f"✅ Stripe payment success for {email} — ${amount}")

        # 🚀 Trigger auto user creation
        try:
            requests.post(
                "https://brainwashlabs.onrender.com/api/auth/auto_create",
                json={"email": email, "plan": "Pro", "source": "Stripe"},
                timeout=10
            )
        except Exception as e:
            print("⚠️ Error creating user:", e)

    return {"status": "ok"}

# ───────────────────────────────────────────────
# ⚙️ Coinbase Webhook
# ───────────────────────────────────────────────
@router.post("/coinbase")
async def coinbase_webhook(request: Request):
    """Coinbase webhook handler for confirmed crypto payments."""
    secret = os.getenv("COINBASE_API_KEY")
    signature = request.headers.get("X-CC-Webhook-Signature", "")
    body = await request.body()

    if not secret:
        raise HTTPException(status_code=400, detail="Coinbase secret missing")

    computed = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(computed, signature):
        raise HTTPException(status_code=400, detail="Invalid Coinbase signature")

    data = json.loads(body)
    event = data.get("event", {})
    event_type = event.get("type", "")
    charge = event.get("data", {})

    if event_type == "charge:confirmed":
        email = charge.get("metadata", {}).get("customer_email") or charge.get("metadata", {}).get("email")
        amount = charge.get("pricing", {}).get("local", {}).get("amount")
        print(f"✅ Coinbase payment success for {email} — ${amount}")

        try:
            requests.post(
                "https://brainwashlabs.onrender.com/api/auth/auto_create",
                json={"email": email, "plan": "Pro", "source": "Coinbase"},
                timeout=10
            )
        except Exception as e:
            print("⚠️ Error creating user:", e)

    return {"status": "ok"}

# ───────────────────────────────────────────────
# 🧠 Health check
# ───────────────────────────────────────────────
@router.get("/status")
async def webhooks_status():
    """Basic webhook router heartbeat."""
    return {
        "webhooks": "✅ active",
        "stripe_secret_loaded": bool(os.getenv("STRIPE_WEBHOOK_SECRET")),
        "coinbase_secret_loaded": bool(os.getenv("COINBASE_API_KEY")),
    }
