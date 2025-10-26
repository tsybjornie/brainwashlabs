from fastapi import APIRouter
import os
import httpx
import logging

router = APIRouter(prefix="/integrations", tags=["Integrations"])
logger = logging.getLogger("brainwashlabs")

async def check_api(name: str, url: str, headers: dict) -> bool:
    """Quickly check if a remote API is reachable."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(url, headers=headers)
            logger.info(f"{name} → {resp.status_code} {resp.reason_phrase}")
            return resp.status_code < 400
    except Exception as e:
        logger.warning(f"{name} check failed: {e}")
        return False

@router.get("/status")
async def integrations_status():
    stripe_key = os.getenv("STRIPE_SECRET_KEY")
    coinbase_key = os.getenv("COINBASE_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    results = {
        "stripe": "⚠️ Missing key" if not stripe_key else "⏳ Checking...",
        "coinbase": "⚠️ Missing key" if not coinbase_key else "⏳ Checking...",
        "openai": "⚠️ Missing key" if not openai_key else "⏳ Checking..."
    }

    if stripe_key:
        ok = await check_api("Stripe", "https://api.stripe.com/v1/charges",
                             {"Authorization": f"Bearer {stripe_key}"})
        results["stripe"] = "✅ Live" if ok else "❌ Invalid key"

    if coinbase_key:
        ok = await check_api("Coinbase", "https://api.commerce.coinbase.com/checkouts",
                             {"X-CC-Api-Key": coinbase_key})
        results["coinbase"] = "✅ Live" if ok else "❌ Invalid key"

    if openai_key:
        ok = await check_api("OpenAI", "https://api.openai.com/v1/models",
                             {"Authorization": f"Bearer {openai_key}"})
        results["openai"] = "✅ Live" if ok else "❌ Invalid key"

    return results
