"""Logged-in user context for API payloads."""

from typing import Optional

from PyQt5.QtCore import QSettings


def get_logged_in_username(default: str = "system") -> str:
    """Return a non-empty username for audit / transaction API fields."""
    settings = QSettings("FactorySystem")
    for key in ("user_name", "username", "email"):
        raw = settings.value(key)
        if raw is None:
            continue
        text = str(raw).strip()
        if text:
            return text
    return default


def enrich_payload_with_user(
    payload: Optional[dict],
    *,
    include_user_name: bool = True,
    include_username: bool = False,
) -> dict:
    """Attach logged-in user fields expected by backend endpoints."""
    data = dict(payload or {})
    name = get_logged_in_username()
    if include_user_name and not str(data.get("user_name", "")).strip():
        data["user_name"] = name
    if include_username and not str(data.get("username", "")).strip():
        data["username"] = name
    return data
