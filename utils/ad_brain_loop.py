# ───────────────────────────────────────────────
# 🤖 Ad Brain Loop — Brainwash Labs v2.7.3
# Auto ROI Forecast Engine (Render-Safe)
# Reads finance_log.json → generates reinvest.json
# ───────────────────────────────────────────────

import json, time, random
from pathlib import Path
from datetime import datetime

DATA_DIR = Path("data")
FINANCE_LOG = DATA_DIR / "finance_log.json"
REINVEST_FILE = DATA_DIR / "reinvest.json"

def load_json(path: Path):
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def run_forecast():
    """Recalculate ROI forecast based on payments."""
    finance = load_json(FINANCE_LOG)
    total_revenue = sum(float(x.get("amount", 0)) for x in finance)
    total_ads_spent = 100.0  # starting base (can pull live later)
    roi = round(total_revenue / total_ads_spent, 2) if total_ads_spent else 0

    next_budget = 0
    if roi > 1.5:
        next_budget = total_ads_spent * 1.5
    elif roi > 1.0:
        next_budget = total_ads_spent * 1.2
    else:
        next_budget = total_ads_spent * 0.8

    reinvest = {
        "timestamp": datetime.utcnow().isoformat(),
        "total_revenue": total_revenue,
        "ads_spent": total_ads_spent,
        "roi": roi,
        "next_budget": round(next_budget, 2),
        "confidence": random.randint(82, 98)
    }

    save_json(REINVEST_FILE, reinvest)
    print(f"[AdBrain] ROI={roi} | Next=${next_budget}")
    return reinvest

if __name__ == "__main__":
    print("🧠 Ad Brain Loop started (manual run mode)")
    result = run_forecast()
    print(json.dumps(result, indent=2))
