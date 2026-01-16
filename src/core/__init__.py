"""
Core module for Economic Policy Engine
Contains configuration, security, and shared utilities
"""

from .config import settings, Settings
from .security import SecurityManager
from .audit import AuditLogger
from .encryption import EncryptionManager

__all__ = [
    "settings",
    "Settings",
    "SecurityManager",
    "AuditLogger",
    "EncryptionManager",
]
