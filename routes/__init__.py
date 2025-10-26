# routes/__init__.py
"""
Force-loads all routers inside /routes during startup.
Ensures Render never skips lazy imports.
"""

from . import auth, avatar, analytics, dashboard, finance, integrations, webhooks

__all__ = ["auth", "avatar", "analytics", "dashboard", "finance", "integrations", "webhooks"]
