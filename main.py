from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from importlib import import_module
from pathlib import Path
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
    version="2.3.0"
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
# 🧩 Dynamic Router Loader (Auto-Prefix Enabled)
# ───────────────────────────────────────────────
routes_path = Path(__file__).parent / "routes"

if routes_path.exists():
    logger.info(f"📁 Scanning for routers in: {routes_path.resolve()}")
    loaded_count = 0
    for file in routes_path.glob("*.py"):
        if file.stem.startswith("_"):
            continue
        try:
            module = import_module(f"routes.{file.stem}")
            if hasattr(module, "router"):
                prefix = f"/{file.stem}" if file.stem != "main" else ""
                app.include_router(module.router, prefix=prefix)
                logger.info(f"✅ Loaded router with prefix: {prefix}")
                loaded_count += 1
            else:
                logger.warning(f"⚠️ {file.stem}.py does not define `router`")
        except Exception as e:
            logger.error(f"❌ Failed to load router {file.stem}: {e}")
    if loaded_count == 0:
        logger.warning("⚠️ No routers were successfully loaded from /routes")
else:
    logger.error("❌ Routes directory not found. Verify deployment path structure.")

# ───────────────────────────────────────────────
# 💡 Root & Health Endpoints
# ───────────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "status": "✅ Brainwash Labs Backend is running!",
        "environment": os.getenv("ENV", "production"),
        "version": "2.3.0",
        "origin": os.getenv("RENDER_EXTERNAL_URL", "local"),
    }

@app.get("/healthz")
async def health_check():
    """Simple Render/Load Balancer probe"""
    return {"ok": True, "uptime": "stable", "env": os.getenv("ENV", "production")}

# ───────────────────────────────────────────────
# ⚙️ Async Service Health Checks (Stripe, Coinbase, OpenAI)
# ───────────────────────────────────────────────
async def verify_service_health():
    services = {
        "Stripe": os.getenv("STRIPE_SECRET_KEY"),
        "Coinbase": os.getenv("COINBASE_API_KEY"),
        "OpenAI": os.getenv("OPENAI_API_KEY")
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
                        headers={"Authorization": f"Bearer {key}"}
                    )
                elif name == "Coinbase":
                    await client.get(
                        "https://api.commerce.coinbase.com/checkouts",
                        headers={"X-CC-Api-Key": key}
                    )
                elif name == "OpenAI":
                    await client.get(
                        "https://api.openai.com/v1/models",
                        headers={"Authorization": f"Bearer {key}"}
                    )
                logger.info(f"✅ {name} API reachable")
            except Exception as e:
                logger.warning(f"⚠️ {name} connectivity check failed: {e}")

# ───────────────────────────────────────────────
# 🧠 Startup Events
# ───────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Booting Brainwash Labs Backend (Render v2.3)")

    # 1. Check environment variables
    missing_envs = [
        k for k in ["STRIPE_SECRET_KEY", "COINBASE_API_KEY", "OPENAI_API_KEY"]
        if not os.getenv(k)
    ]
    if missing_envs:
        logger.warning(f"⚠️ Missing ENV variables: {', '.join(missing_envs)}")
    else:
        logger.info("✅ All critical ENV variables found")

    # 2. Verify third-party services concurrently
    asyncio.create_task(verify_service_health())

    logger.info("🧩 Backend initialized successfully and ready for requests.")

# ───────────────────────────────────────────────
# 🧩 Debug Endpoint (safe inspection)
# ───────────────────────────────────────────────
@app.get("/debug/env")
async def debug_env():
    """Safe environment view for Render AI debug"""
    safe_routes = [r.path for r in app.routes if hasattr(r, "path")]
    safe_envs = [
        k for k in os.environ.keys()
        if not any(x in k.lower() for x in ["key", "secret", "token"])
    ]
    return {
        "service": "Brainwash Labs Backend",
        "env_keys": safe_envs,
        "routes_loaded": safe_routes,
        "version": "2.3.0"
    }
