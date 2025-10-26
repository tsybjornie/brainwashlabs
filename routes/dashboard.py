# ───────────────────────────────────────────────
# 📊 Dashboard Router — Brainwash Labs v2.6.2
# Integrates Finance + Webhook analytics
# ───────────────────────────────────────────────

from fastapi import APIRouter
import json, os
from pathlib import Path
from datetime import datetime

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

DATA_PATH = Path("data/finance_log.json")

# ───────────────────────────────────────────────
# 📁 Helpers for loading finance data
# ───────────────────────────────────────────────
def load_finance_data():
    if not DATA_PATH.exists():
        return {
            "transactions": [],
            "total_revenue_usd": 0,
            "stripe_payments": 0,
            "coinbase_payments": 0,
        }

    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
    except Exception as e:
        print(f"⚠️ Failed to load finance data: {e}")

    return {
        "transactions": [],
        "total_revenue_usd": 0,
        "stripe_payments": 0,
        "coinbase_payments": 0,
    }

# ───────────────────────────────────────────────
# 📈 Dashboard Metrics Endpoint
# ───────────────────────────────────────────────
@router.get("/metrics")
async def dashboard_metrics():
    """Return live dashboard analytics."""
    data = load_finance_data()

    total_tx = len(data.get("transactions", []))
    total_revenue = data.get("total_revenue_usd", 0)
    stripe_count = data.get("stripe_payments", 0)
    coinbase_count = data.get("coinbase_payments", 0)

    return {
        "dashboard": "✅ active",
        "total_transactions": total_tx,
        "total_revenue_usd": total_revenue,
        "stripe_payments": stripe_count,
        "coinbase_payments": coinbase_count,
        "env": os.getenv("ENV", "production"),
        "version": "v2.6.2",
        "last_updated": datetime.utcnow().isoformat() + "Z"
    }

# ───────────────────────────────────────────────
# 🩵 Dashboard Health Endpoint
# ───────────────────────────────────────────────
@router.get("/status")
async def dashboard_status():
    """Simple health check for dashboard router."""
    return {
        "dashboard": "✅ ready",
        "env": os.getenv("ENV", "production"),
        "version": "v2.6.2",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
