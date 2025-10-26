from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os, logging, asyncio, httpx
from importlib import import_module
from pathlib import Path

# ───────────────────────────────────────────────
# 🧩 Environment Boot
# ───────────────────────────────────────────────
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("brainwashlabs")

# ───────────────────────────────────────────────
# 🚀 FastAPI App
# ───────────────────────────────────────────────
app = FastAPI(
    title="🧠 Brainwash Labs Backend",
    description="Autonomous SaaS Factory Backend — Render Live Environment",
    version="2.4.1"
)

# ───────────────────────────────────────────────
# 🌐 CORS
# ───────────────────────────────────────────────
default_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://brainwashlabs.onrender.com",
    "https://brainwashlabs.com",
]
extra_origins = os.getenv("CORS_EXTRA_ORIGINS", "")
if extra_origins:
    default_origins.extend(extra_origins.split(","))

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in default_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ───────────────────────────────────────────────
# 💡 Base Routes
# ───────────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "status": "✅ Brainwash Labs Backend is running!",
        "env": os.getenv("ENV", "production"),
        "version": "2.4.1"
    }

@app.get("/healthz")
async def health_check():
    return {"ok": True, "uptime": "stable", "env": os.getenv("ENV", "production")}

# ───────────────────────────────────────────────
# 🧠 Service Health Checks
# ───────────────────────────────────────────────
async def verify_service_health():
    services = {
        "Stripe": os.getenv("STRIPE_SECRET_KEY"),
        "Coinbase": os.getenv("COINBASE_API_KEY"),
        "OpenAI": os.getenv("OPENAI_API_KEY"),
    }
    async with httpx.AsyncClient(timeout=6.0) as client:
        for name, key in services.items():
            if not key:
                logger.warning(f"⚠️ Missing {name} API key in environment")
                continue
            try:
                urls = {
                    "Stripe": "https://api.stripe.com/v1/charges",
                    "Coinbase": "https://api.commerce.coinbase.com/checkouts",
                    "OpenAI": "https://api.openai.com/v1/models"
                }
                await client.get(urls[name], headers={
                    "Authorization": f"Bearer {key}" if name != "Coinbase" else "",
                    "X-CC-Api-Key": key if name == "Coinbase" else ""
                })
                logger.info(f"✅ {name} API reachable")
            except Exception as e:
                logger.warning(f"⚠️ {name} connectivity check failed: {e}")

# ───────────────────────────────────────────────
# 🧩 Force Import + Router Registration
# ───────────────────────────────────────────────
try:
    import routes
    from routes import (
        auth, avatar, analytics, dashboard, finance, integrations, webhooks
    )

    app.include_router(auth.router, prefix="/auth")
    app.include_router(avatar.router, prefix="/avatar")
    app.include_router(analytics.router, prefix="/analytics")
    app.include_router(dashboard.router, prefix="/dashboard")
    app.include_router(finance.router, prefix="/finance")
    app.include_router(integrations.router, prefix="/integrations")
    app.include_router(webhooks.router, prefix="/webhooks")

    logger.info("✅ All routers registered successfully (hard-load mode).")
except Exception as e:
    logger.error(f"❌ Router registration failed: {e}")

# ───────────────────────────────────────────────
# 🧩 Debug
# ───────────────────────────────────────────────
@app.get("/debug/routes")
async def debug_routes():
    return {
        "routes": [r.path for r in app.routes if hasattr(r, "path")],
        "version": "2.4.1"
    }

# ───────────────────────────────────────────────
# 🧠 Startup
# ───────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Booting Brainwash Labs Backend (v2.4.1)")
    asyncio.create_task(verify_service_health())
    logger.info("🧩 Backend initialized and ready for requests.")
