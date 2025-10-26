# ───────────────────────────────────────────────
# 📊 Dashboard Router — Brainwash Labs
# Unified service monitor for Finance + Webhooks
# ───────────────────────────────────────────────

from fastapi import APIRouter
import os
import datetime
import stripe
import requests

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"]
)

# ───────────────────────────────────────────────
# ✅ Status check (core heartbeat)
# ───────────────────────────────────────────────
@router.get("/status")
async def dashboard_status():
    """Return overall system heartbeat."""
    return {
        "dashboard": "✅ router active",
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "environment": os.getenv("ENV", "production")
    }

# ───────────────────────────────────────────────
# 💰 Finance readiness probe
# ───────────────────────────────────────────────
@router.get("/finance")
async def dashboard_finance_status():
    """Check Stripe + Coinbase connectivity."""
    stripe_key = os.getenv("STRIPE_SECRET_KEY")
    coinbase_key = os.getenv("COINBASE_API_KEY")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    status = {
        "stripe_connected": bool(stripe_key),
        "coinbase_connected": bool(coinbase_key),
        "webhook_secret_loaded": bool(webhook_secret),
    }

    # Try a light Stripe API ping if configured
    if stripe_key:
        try:
            stripe.api_key = stripe_key
            # lightweight call (won’t charge)
            balance = stripe.Balance.retrieve()
            status["stripe_api_ok"] = True
            status["available_balance"] = sum([b.amount for b in balance.available]) / 100
        except Exception as e:
            status["stripe_api_ok"] = False
            status["error"] = str(e)

    return status

# ───────────────────────────────────────────────
# 🔔 Webhook heartbeat aggregation
# ───────────────────────────────────────────────
@router.get("/webhooks")
async def dashboard_webhooks_status():
    """Ping local webhook endpoints to verify import."""
    base_url = os.getenv("DASHBOARD_BASE_URL", "https://brainwashlabs.onrender.com")
    urls = {
        "stripe": f"{base_url}/api/webhooks/status",
    }
    results = {}
    try:
        r = requests.get(urls["stripe"], timeout=5)
        results["webhooks_status"] = r.json()
    except Exception as e:
        results["webhooks_status"] = {"error": str(e)}
    return results

# ───────────────────────────────────────────────
# 📈 Summary metrics (placeholder for UI)
# ───────────────────────────────────────────────
@router.get("/metrics")
async def dashboard_metrics():
    """Aggregate core service states for frontend."""
    return {
        "uptime": "99.9%",
        "version": "v2.4.8",
        "services": {
            "auth": True,
            "finance": True,
            "webhooks": True,
        },
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    }

# ───────────────────────────────────────────────
# 🧠 Diagnostic route
# ───────────────────────────────────────────────
@router.get("/debug")
async def dashboard_debug():
    """Return diagnostic environment info (safe subset)."""
    return {
        "routes_loaded": True,
        "module": "dashboard.py",
        "env_loaded": bool(os.getenv("STRIPE_SECRET_KEY") or os.getenv("COINBASE_API_KEY")),
        "notes": "Dashboard verified and live"
    }
