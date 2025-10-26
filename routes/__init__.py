# routes/__init__.py
"""
✅ Brainwash Labs Route Registry — Render-Proof Loader (v2.4.2)
Ensures all routers inside /routes are imported during startup.
"""

import importlib
import logging

logger = logging.getLogger("routes")

ROUTE_MODULES = [
    "auth",
    "avatar",
    "analytics",
    "dashboard",
    "finance",
    "integrations",
    "webhooks"
]

loaded = []

for module_name in ROUTE_MODULES:
    try:
        imported = importlib.import_module(f"routes.{module_name}")
        if hasattr(imported, "router"):
            loaded.append(module_name)
            logger.info(f"✅ Router imported: {module_name}")
        else:
            logger.warning(f"⚠️ No router found in {module_name}.py")
    except Exception as e:
        logger.error(f"❌ Failed to import {module_name}: {e}")

if not loaded:
    logger.warning("⚠️ No routers successfully loaded. Check Render folder mapping.")

__all__ = loaded
