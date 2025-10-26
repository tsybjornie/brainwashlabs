# ───────────────────────────────────────────────
# 📊 Analytics Router — Brainwash Labs v2.7.4
# Pulls ROI forecast + finance metrics for dashboard
# ───────────────────────────────────────────────

from fastapi import APIRouter
from pathlib import Path
import json

router = APIRouter(tags=["Analytics"])

DATA_DIR = Path("data")
FINANCE_LOG = DATA_DIR / "finance_log.json"
REINVEST_FILE = DATA_DIR / "reinvest.json"

def load_json(path: Path, default=None):
    if not path.exists():
        return default or {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default or {}

@router.get("/roi")
async def get_roi_forecast():
    """Return live ROI + next ad budget from reinvest.json."""
    reinvest = load_json(REINVEST_FILE, {})
    return {
        "total_revenue": reinvest.get("total_revenue", 0),
        "ads_spent": reinvest.get("ads_spent", 0),
        "roi": reinvest.get("roi", 0),
        "next_budget": reinvest.get("next_budget", 0),
        "confidence": reinvest.get("confidence", 0),
        "timestamp": reinvest.get("timestamp", "N/A"),
        "version": "v2.7.4"
    }
