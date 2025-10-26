import sys, os, logging, asyncio, httpx, traceback
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# ───────────────────────────────────────────────
# 🧩 Environment Boot + Render Path Safety
# ───────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

print("📦 Python path:", sys.path)
print("📁 Routes folder exists:", os.path.exists(os.path.join(BASE_DIR, "routes")))
print("📁 Routes init found:", os.path.exists(os.path.join(BASE_DIR, "routes", "__init__.py")))

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
    version="2.4.5"
)

# ───────────────────────────────────────────────
# 🌐 CORS Setup
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
# 💡 Root + Health Endpoints
# ───────────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "status": "✅ Brainwash Labs Backend is running!",
        "env": os.getenv("ENV", "production"),
        "version": "2.4.5",
    }

@app.get("/healthz")
async def health_check():
    return {"ok": True, "uptime": "stable", "env": os.getenv("ENV", "production")}

# ───────────────────────────────────────────────
# ⚙️ Third-Party Service Health (Async)
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
                    "OpenAI": "https://api.openai.com/v1/models",
                }
                headers = {
                    "Authorization": f"Bearer {key}" if name != "Coinbase" else "",
                    "X-CC-Api-Key": key if name == "Coinbase" else "",
                }
                await client.get(urls[name], headers=headers)
                logger.info(f"✅ {name} API reachable")
            except Exception as e:
                logger.warning(f"⚠️ {name} connectivity check failed: {e}")

# ───────────────────────────────────────────────
# 🧩 Router Registration (Force-Load & Diagnose)
# ───────────────────────────────────────────────
try:
    import routes
    from routes import auth, avatar, analytics, dashboard, finance, integrations, webhooks

    routers = {
        "/auth": auth,
        "/avatar": avatar,
        "/analytics": analytics,
        "/dashboard": dashboard,
        "/finance": finance,
        "/integrations": integrations,
        "/webhooks": webhooks,
    }

    for prefix, module in routers.items():
        if hasattr(module, "router"):
            app.include_router(module.router, prefix=prefix)
            logger.info(f"✅ Registered router: {prefix}")
        else:
            logger.warning(f"⚠️ Skipped {prefix}: no `router` found")

    logger.info("🚀 All routers registered successfully (v2.4.5)")

except Exception as e:
    logger.error(f"❌ Router registration failed: {e}")
    traceback.print_exc()

# ───────────────────────────────────────────────
# 🧩 Debug Endpoint — Route Map
# ───────────────────────────────────────────────
@app.get("/debug/routes")
async def debug_routes():
    return {
        "routes": [r.path for r in app.routes if hasattr(r, "path")],
        "version": "2.4.5",
    }

# ───────────────────────────────────────────────
# 🚀 Startup Hook
# ───────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Booting Brainwash Labs Backend (v2.4.5)")
    asyncio.create_task(verify_service_health())
    logger.info("🧩 Backend initialized and ready for requests.")
