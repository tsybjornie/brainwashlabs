# ───────────────────────────────────────────────
# ⚡ Webhooks Router — Brainwash Labs (v2.7.2)
# Stripe + Coinbase payment confirmations
# Auto-sync with finance_log.json + Render-safe
# ───────────────────────────────────────────────

from fastapi import APIRouter, Request, HTTPException, Header
from pathlib import Path
from datetime import datetime
import json, os, stripe, logging

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

DATA_DIR = Path("data")
WEBHOOK_LOG = DATA_DIR / "webhook_log.json"
FINANCE_LOG = DATA_DIR / "finance_log.json"

# ───────────────────────────────────────────────
# 🧾 Helpers
# ───────────────────────────────────────────────
def safe_load_json(path: Path):
    """Safely read JSON or return default."""
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def safe_write_json(path: Path, data):
    """Safely write JSON data (atomic + limited)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data[-100:], f, indent=2)
    except Exception as e:
        logger.error(f"❌ Failed to write {path}: {e}")

def append_log(source: str, payload: dict):
    """Append to webhook_log.json (for diagnostics)."""
    logs = safe_load_json(WEBHOOK_LOG)
    logs.append({
        "source": source,
        "timestamp": datetime.utcnow().isoformat(),
        "payload": payload
    })
    safe_write_json(WEBHOOK_LOG, logs)

def append_finance(source: str, email: str, amount: float, txid: str):
    """Append to finance_log.json for metrics sync."""
    data = safe_load_json(FINANCE_LOG)
    data.append({
        "id": txid,
        "email": email,
        "amount": amount,
        "source": source,
        "timestamp": datetime.utcnow().isoformat(),
    })
    safe_write_json(FINANCE_LOG, data)
    logger.info(f"💾 Finance entry added ({source}) ${amount} → {email}")

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
        raise HTTPException(status_code=400, detail="Stripe webhook secret missing")

    payload = await request.body()

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=stripe_signature,
            secret=STRIPE_WEBHOOK_SECRET
        )

        event_type = event.get("type")
        data = event.get("data", {}).get("object", {})
        append_log("stripe", data)
        logger.info(f"✅ Stripe event received: {event_type}")

        if event_type == "checkout.session.completed":
            email = data.get("customer_email")
            total = float(data.get("amount_total", 0)) / 100
            txid = data.get("id")
            append_finance("stripe", email, total, txid)
            logger.info(f"💰 Stripe checkout complete for {email} (${total})")

        return {"ok": True, "event": event_type, "source": "stripe"}

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
        event = body.get("event", {})
        event_type = event.get("type", "unknown")
        data = event.get("data", {})

        append_log("coinbase", data)
        logger.info(f"✅ Coinbase event: {event_type}")

        if event_type == "charge:confirmed":
            email = data.get("metadata", {}).get("email")
            pricing = data.get("pricing", {}).get("local", {})
            amount = float(pricing.get("amount", 0))
            txid = data.get("id")
            append_finance("coinbase", email, amount, txid)
            logger.info(f"💰 Coinbase payment confirmed for {email} (${amount})")

        return {"ok": True, "source": "coinbase", "event": event_type}

    except Exception as e:
        logger.error(f"❌ Coinbase webhook error: {e}")
        raise HTTPException(status_code=500, detail=f"Webhook error: {str(e)}")

# ───────────────────────────────────────────────
# 🔍 WEBHOOK STATUS
# ───────────────────────────────────────────────
@router.get("/status")
async def webhook_status():
    """Health check for webhook + finance sync."""
    webhook_logs = safe_load_json(WEBHOOK_LOG)
    finance_logs = safe_load_json(FINANCE_LOG)

    return {
        "webhooks": "✅ active",
        "stripe_configured": bool(STRIPE_WEBHOOK_SECRET),
        "coinbase_configured": bool(COINBASE_API_KEY),
        "webhook_entries": len(webhook_logs),
        "finance_entries": len(finance_logs),
        "version": "v2.7.2",
    }
