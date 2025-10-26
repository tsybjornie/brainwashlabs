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
    version="2.3.2"
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
# 🧠 Dynamic Router Loader (Auto + Fallback)
# ───────────────────────────────────────────────
routes_path = Path(__file__).parent / "routes"
loaded_routes = []

if routes_path.exists():
    logger.info(f"📁 Scanning for routers in: {routes_path.resolve()}")
    for file in routes_path.glob("*.py"):
        if file.stem.startswith("_"):
            continue
        try:
            module = import_module(f"routes.{file.stem}")
            if hasattr(module, "router"):
                prefix = f"/{file.stem}" if file.stem != "main" else ""
                app.include_router(module.router, prefix=prefix)
                loaded_routes.append(f"{prefix or '/'}")
                logger.info(f"✅ Loaded router: {file.stem} (prefix '{prefix}')")
            else:
                logger.warning(f"⚠️ Skipped {file.stem}: no `router` found")
        except Exception as e:
            logger.error(f"❌ Failed to load router {file.stem}: {e}")
else:
    logger.error("❌ Routes directory not found. Verify deployment path structure.")

if not loaded_routes:
    logger.warning("⚠️ No routers successfully loaded — fallback import triggered.")
    try:
        import routes  # triggers registry import from __init__.py
        logger.info("✅ Fallback import from routes.__init__ successful.")
    except Exception as e:
        logger.error(f"❌ Fallback import failed: {e}")

# ───────────────────────────────────────────────
# 💡 Root & Health Endpoints
# ───────────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "status": "✅ Brainwash Labs Backend is running!",
        "environment": os.getenv("ENV", "production"),
        "version": "2.3.2",
        "origin": os.getenv("RENDER_EXTERNAL_URL", "local"),
    }

@app.get("/healthz")
async def health_check():
    return {"ok": True, "uptime": "stable", "env": os.getenv("ENV", "production")}

# ───────────────────────────────────────────────
# ⚙️ Async Service Health Checks
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
    logger.info("🚀 Booting Brainwash Labs Backend (Render v2.3.2)")
    asyncio.create_task(verify_service_health())
    logger.info("🧩 Backend initialized and ready for requests.")

# ───────────────────────────────────────────────
# 🧩 Debug Endpoints
# ───────────────────────────────────────────────
@app.get("/debug/routes")
async def debug_routes():
    """List all registered routes (for Render diagnostics)"""
    return {
        "routes": [r.path for r in app.routes if hasattr(r, "path")],
        "loaded": loaded_routes,
        "version": "2.3.2"
    }
