# ───────────────────────────────────────────────
# 📊 Dashboard Router — Brainwash Labs (v2.6.0)
# Aggregates data from Finance + Webhooks + Local Logs
# Render-safe and analytics-ready
# ───────────────────────────────────────────────

from fastapi import APIRouter, HTTPException
import json, os
from pathlib import Path
from datetime import datetime

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

FINANCE_LOG = Path("data/finance_log.json")
WEBHOOK_LOG = Path("data/webhook_log.json")

# ───────────────────────────────────────────────
# 🧩 Helpers
# ───────────────────────────────────────────────
def safe_load(path: Path):
    try:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return []

def safe_save(path: Path, data: list):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# ───────────────────────────────────────────────
# 💰 Finance Sync (triggered by webhook)
# ───────────────────────────────────────────────
def sync_from_webhooks():
    """Merge Stripe + Coinbase events into finance_log.json"""
    logs = safe_load(WEBHOOK_LOG)
    finance = safe_load(FINANCE_LOG)

    existing_ids = {x.get("id") for x in finance}
    for event in logs:
        payload = event.get("payload", {})
        pid = payload.get("id") or payload.get("code")
        if not pid or pid in existing_ids:
            continue
        finance.append({
            "id": pid,
            "source": event.get("source"),
            "amount": payload.get("amount", {}).get("amount")
                      if "amount" in payload else None,
            "currency": payload.get("amount", {}).get("currency", "USD")
                      if "amount" in payload else "USD",
            "email": payload.get("metadata", {}).get("email")
                      if "metadata" in payload else None,
            "timestamp": datetime.utcnow().isoformat()
        })

    safe_save(FINANCE_LOG, finance)
    return finance

# ───────────────────────────────────────────────
# 📈 Dashboard Metrics Endpoint
# ───────────────────────────────────────────────
@router.get("/metrics")
async def dashboard_metrics():
    """Aggregate payment data for dashboard display."""
    finance_data = sync_from_webhooks()
    total_tx = len(finance_data)
    total_revenue = sum(float(x.get("amount", 0) or 0) for x in finance_data)
    stripe_tx = [x for x in finance_data if x.get("source") == "stripe"]
    coinbase_tx = [x for x in finance_data if x.get("source") == "coinbase"]

    return {
        "dashboard": "✅ active",
        "total_transactions": total_tx,
        "total_revenue_usd": round(total_revenue, 2),
        "stripe_payments": len(stripe_tx),
        "coinbase_payments": len(coinbase_tx),
        "version": "v2.6.0",
        "env": os.getenv("ENV", "production")
    }

# ───────────────────────────────────────────────
# 🔍 Dashboard Health
# ───────────────────────────────────────────────
@router.get("/status")
async def dashboard_status():
    return {"dashboard": "✅ active", "version": "v2.6.0"}
