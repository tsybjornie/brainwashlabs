from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from importlib import import_module
from pathlib import Path
from dotenv import load_dotenv
import os
import logging

# ───────────────────────────────────────────────
# 🧩 Environment Boot
# ───────────────────────────────────────────────
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("brainwashlabs")

# ───────────────────────────────────────────────
# 🚀 FastAPI App Setup
# ───────────────────────────────────────────────
app = FastAPI(
    title="🧠 Brainwash Labs Backend",
    description="Autonomous SaaS Factory Backend — Render Live Environment",
    version="1.1.0"
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

# Allow dynamic whitelisting via ENV
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
# 🧩 Auto-load Routers (any file inside /routes)
# ───────────────────────────────────────────────
routes_path = Path(__file__).parent / "routes"

for file in routes_path.glob("*.py"):
    if file.stem.startswith("_"):
        continue
    try:
        module = import_module(f"routes.{file.stem}")
        if hasattr(module, "router"):
            app.include_router(module.router)
            logger.info(f"✅ Loaded router: {file.stem}")
    except Exception as e:
        logger.warning(f"⚠️ Could not load router {file.stem}: {e}")

# ───────────────────────────────────────────────
# 💡 Root & Health Endpoints
# ───────────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "status": "✅ Brainwash Labs Backend is running!",
        "environment": os.getenv("ENV", "production"),
        "version": "1.1.0",
    }

@app.get("/healthz")
async def health_check():
    return {"ok": True, "uptime": "stable", "env": os.getenv("ENV", "production")}

# ───────────────────────────────────────────────
# 🧠 Startup Logs
# ───────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    missing_envs = [
        key for key in ["STRIPE_SECRET_KEY", "COINBASE_API_KEY", "OPENAI_API_KEY"]
        if not os.getenv(key)
    ]
    if missing_envs:
        logger.warning(f"⚠️ Missing ENV variables: {', '.join(missing_envs)}")
    else:
        logger.info("✅ All critical ENV variables found")

    logger.info("🚀 Brainwash Labs Backend initialized successfully!")
