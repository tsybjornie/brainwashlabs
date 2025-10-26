from fastapi import APIRouter
import time, random

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/pulse")
async def analytics_pulse():
    return {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "active_users": random.randint(50, 200),
        "transactions": random.randint(10, 50),
        "system": "✅ Stable"
    }
