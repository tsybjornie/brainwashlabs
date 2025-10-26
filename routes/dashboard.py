# ───────────────────────────────────────────────
# routes/dashboard.py — v2.7.0
# Finance + ROI Dashboard Router
# ───────────────────────────────────────────────
from fastapi import APIRouter
from pathlib import Path
import json, os

router = APIRouter()
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
FINANCE_LOG = DATA_DIR / "finance_log.json"
REINVEST_LOG = DATA_DIR / "reinvest.json"

def read_json(file_path):
    if not file_path.exists():
        return []
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except:
        return []

@router.get("/status")
async def dashboard_status():
    return {
        "ok": True,
        "finance_connected": FINANCE_LOG.exists(),
        "environment": os.getenv("ENV", "production"),
        "version": "v2.7.0"
    }

@router.get("/metrics")
async def dashboard_metrics():
    logs = read_json(FINANCE_LOG)
    total_revenue = 0
    stripe_rev = 0
    coinbase_rev = 0

    if isinstance(logs, list):
        for tx in logs:
            amt = float(tx.get("amount", 0))
            total_revenue += amt
            src = tx.get("source", "").lower()
            if "stripe" in src:
                stripe_rev += amt
            elif "coinbase" in src:
                coinbase_rev += amt

    roi_data = read_json(REINVEST_LOG)
    roi = roi_data.get("roi", 0) if isinstance(roi_data, dict) else 0

    return {
        "total_revenue": round(total_revenue, 2),
        "stripe_revenue": round(stripe_rev, 2),
        "coinbase_revenue": round(coinbase_rev, 2),
        "roi": round(roi, 2),
        "version": "v2.7.0"
    }
