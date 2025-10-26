# main.py — Brainwash Labs Backend (v2.4.0 Render-Proof Edition)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import logging
import httpx
import asyncio

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
# 🚀 FastAPI App Setup
# ───────────────────────────────────────────────
app = FastAPI(
    title="🧠 Brainwash Labs Backend",
    description="Autonomous SaaS Factory Backend — Render Live Environment",
    version="2.4.0"
)

# ───────────────────────────────────────────────
# 🌐 CORS Configuration
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
# 🧠 ROUTER REGISTRATION (Render-Proof Method)
# ───────────────────────────────────────────────
# Render sometimes skips dynamic imports, so we hard-register all routers.
try:
    from routes import (
        auth,
        avatar,
        analytics,
        dashboard,
        finance,
        integrations,
        webhooks,
    )

    app.include_router(auth.router)
    app.include_router(avatar.router)
    app.include_router(analytics.router)
    app.include_router(dashboard.router)
    app.include_router(finance.router)
    app.include_router(integrations.router)
    app.include_router(webhooks.router)

    logger.info("✅ All routers manually registered successfully.")
except Exception as e:
    logger.error(f"❌ Router import failed: {e}")

# ───────────────────────────────────────────────
# 💡 Root & Health Endpoints
# ───────────────────────────────────────────────
@app.get("/")
async def root():
    """Main landing endpoint"""
    return {
        "status": "✅ Brainwash Labs Backend is running!",
        "environment": os.getenv("ENV", "production"),
        "version": "2.4.0",
        "origin": os.getenv("RENDER_EXTERNAL_URL", "local"),
    }

@app.get("/healthz")
async def health_check():
    """Render health check endpoint"""
    return {"ok": True, "uptime": "stable", "env": os.getenv("ENV", "production")}

# ───────────────────────────────────────────────
# ⚙️ Async Service Health Checks (Stripe / Coinbase / OpenAI)
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
                if name == "Stripe":
                    await client.get(
                        "https://api.stripe.com/v1/charges",
                        headers={"Authorization": f"Bearer {key}"},
                    )
                elif name == "Coinbase":
                    await client.get(
                        "https://api.commerce.coinbase.com/checkouts",
                        headers={"X-CC-Api-Key": key},
                    )
                elif name == "OpenAI":
                    await client.get(
                        "https://api.openai.com/v1/models",
                        headers={"Authorization": f"Bearer {key}"},
                    )
                logger.info(f"✅ {name} API reachable")
            except Exception as e:
                logger.warning(f"⚠️ {name} connectivity check failed: {e}")

# ───────────────────────────────────────────────
# 🧠 Startup Events
# ───────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Booting Brainwash Labs Backend (Render v2.4.0)")
    asyncio.create_task(verify_service_health())
    logger.info("🧩 Backend initialized and ready for requests.")

# ───────────────────────────────────────────────
# 🧩 Debug Endpoints
# ───────────────────────────────────────────────
@app.get("/debug/routes")
async def debug_routes():
    """List all registered routes for Render diagnostics"""
    try:
        return {
            "routes": [r.path for r in app.routes if hasattr(r, "path")],
            "version": "2.4.0",
        }
    except Exception as e:
        return {"error": str(e)}
