# routes/__init__.py
"""
✅ Brainwash Labs — Route Registry (v2.4.3)
Forces import of all routers in /routes during startup, even on Render.
"""

import importlib
import logging
import os

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

loaded = []

# Verify routes directory existence
routes_dir = os.path.dirname(__file__)
logger.info(f"📁 Verifying routes in: {routes_dir}")

for module_name in ROUTE_MODULES:
    try:
        module = importlib.import_module(f"routes.{module_name}")
        if hasattr(module, "router"):
            loaded.append(module_name)
            logger.info(f"✅ Router imported: {module_name}")
        else:
            logger.warning(f"⚠️ No 'router' found in {module_name}.py")
    except ModuleNotFoundError:
        logger.warning(f"⚠️ Missing file: routes/{module_name}.py")
    except Exception as e:
        logger.error(f"❌ Error importing {module_name}: {e}")

if loaded:
    logger.info(f"✅ Routers loaded successfully: {', '.join(loaded)}")
else:
    logger.error("❌ No routers loaded — please check router files.")

__all__ = loaded
