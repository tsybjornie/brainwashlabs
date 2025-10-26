"""
🧩 Router Package Initializer — Brainwash Labs Backend v2.4.0
Ensures all route modules inside /routes are force-loaded at startup.
This prevents Render from skipping lazy imports and guarantees
each router (auth, finance, integrations, etc.) is registered properly.
"""

# Import all route modules
from . import (
    auth,
    avatar,
    analytics,
    dashboard,
    finance,
    integrations,
    webhooks
)

# Expose routers explicitly (for debugging or manual registration)
__all__ = [
    "auth",
    "avatar",
    "analytics",
    "dashboard",
    "finance",
    "integrations",
    "webhooks",
]

# Optional: helper for diagnostics
def list_routes():
    """Return all routers successfully imported"""
    return [m for m in __all__ if m in globals()]

# Log confirmation on import (useful for Render boot logs)
if __name__ == "__main__" or True:
    print(f"✅ routes/__init__.py loaded. Modules: {', '.join(list_routes())}")
