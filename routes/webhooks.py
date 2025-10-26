# ───────────────────────────────────────────────
# ⚡ Webhooks Router — Brainwash Labs (v2.6.0)
# Stripe + Coinbase payment confirmation
# Render-safe, idempotent + structured logging
# ───────────────────────────────────────────────

from fastapi import APIRouter, Request, HTTPException, Header
import stripe
import json
import logging
import os
from pathlib import Path
from datetime import datetime

# ───────────────────────────────────────────────
# 🧩 Router Init
# ───────────────────────────────────────────────
router = APIRouter(tags=["Webhooks"])
logger = logging.getLogger("brainwashlabs.webhooks")

# ───────────────────────────────────────────────
# 🔐 Load Keys
# ───────────────────────────────────────────────
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
COINBASE_API_KEY = os.getenv("COINBASE_API_KEY")

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY

LOG_PATH = Path("data/webhook_log.json")

# ───────────────────────────────────────────────
# 🧾 Local Log Helper
# ───────────────────────────────────────────────
def append_log(source: str, payload: dict):
    """Store webhook logs safely."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    logs = []
    if LOG_PATH.exists():
        try:
            with open(LOG_PATH, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except Exception:
            pass
    logs.append({
        "source": source,
        "timestamp": datetime.utcnow().isoformat(),
        "payload": payload
    })
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(logs[-100:], f, indent=2)  # keep last 100 entries

# ───────────────────────────────────────────────
# 💳 STRIPE WEBHOOK HANDLER
# ───────────────────────────────────────────────
@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature")
):
    """Handle Stripe webhook events."""
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=400, detail="Stripe webhook secret not configured")

    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=stripe_signature,
            secret=STRIPE_WEBHOOK_SECRET
        )
        event_type = event["type"]
        data = event["data"]["object"]
        logger.info(f"✅ Stripe event received: {event_type}")
        append_log("stripe", data)

        # Optional: Handle specific event types
        if event_type == "checkout.session.completed":
            email = data.get("customer_email")
            logger.info(f"💰 Stripe checkout completed for {email}")

        return {"ok": True, "source": "stripe", "event": event_type}

    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid Stripe signature")
    except Exception as e:
        logger.error(f"❌ Stripe webhook error: {e}")
        raise HTTPException(status_code=500, detail=f"Webhook error: {str(e)}")

# ───────────────────────────────────────────────
# 🪙 COINBASE WEBHOOK HANDLER
# ───────────────────────────────────────────────
@router.post("/coinbase")
async def coinbase_webhook(request: Request):
    """Handle Coinbase Commerce webhook events."""
    try:
        body = await request.json()
        event_type = body.get("event", {}).get("type", "unknown")
        data = body.get("event", {}).get("data", {})
        logger.info(f"✅ Coinbase event: {event_type}")
        append_log("coinbase", data)

        if event_type == "charge:confirmed":
            email = data.get("metadata", {}).get("email")
            logger.info(f"💰 Coinbase payment confirmed for {email}")

        return {"ok": True, "source": "coinbase", "event": event_type}

    except Exception as e:
        logger.error(f"❌ Coinbase webhook error: {e}")
        raise HTTPException(status_code=500, detail=f"Webhook error: {str(e)}")

# ───────────────────────────────────────────────
# 🔍 WEBHOOK STATUS ENDPOINT
# ───────────────────────────────────────────────
@router.get("/status")
async def webhook_status():
    """Confirm webhook router is live and logging."""
    total_logs = 0
    if LOG_PATH.exists():
        try:
            with open(LOG_PATH, "r", encoding="utf-8") as f:
                total_logs = len(json.load(f))
        except Exception:
            total_logs = -1

    return {
        "webhooks": "✅ active",
        "stripe_configured": bool(STRIPE_WEBHOOK_SECRET),
        "coinbase_configured": bool(COINBASE_API_KEY),
        "log_entries": total_logs,
        "version": "v2.6.0"
    }
