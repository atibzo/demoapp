# backend/app/__init__.py
"""
Intraday Co-Pilot backend package.

Exports:
- redis_client: Redis connection factory
- get_kite: Zerodha Kite session accessor
"""

from .rl import redis_client  # noqa: F401
from .kite import get_kite    # noqa: F401

__all__ = ["redis_client", "get_kite"]