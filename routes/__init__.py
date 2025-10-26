# routes/__init__.py
"""
✅ Brainwash Labs Router Loader (v2.4.4)
Forces router import at runtime even on Render cold starts.
"""

import importlib
import logging
import os, sys

logger = logging.getLogger("routes")

ROUTE_MODULES = [
    "auth",
    "avatar",
    "analytics",
    "dashboard",
    "finance",
    "integrations",
    "webhooks",
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

logger.info(f"🧭 Router registry active — scanning {BASE_DIR}")

loaded = []

for module_name in ROUTE_MODULES:
    try:
        module = importlib.import_module(f"routes.{module_name}")
        if hasattr(module, "router"):
            loaded.append(module_name)
            logger.info(f"✅ Router imported: {module_name}")
        else:
            logger.warning(f"⚠️ No router defined in {module_name}.py")
    except ModuleNotFoundError:
        logger.warning(f"⚠️ Missing: routes/{module_name}.py")
    except Exception as e:
        logger.error(f"❌ Failed to import {module_name}: {e}")

if loaded:
    logger.info(f"✅ Routers loaded successfully: {', '.join(loaded)}")
else:
    logger.error("❌ No routers imported — check routes folder or init order.")

__all__ = loaded
