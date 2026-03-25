"""
HTTP client for the FastAPI bridge running on the VPS.
All Streamlit pages talk to the backend exclusively through these functions.
If the bridge is unreachable, functions return a BridgeError so pages can
show st.error() instead of crashing.
"""
import logging
from dataclasses import dataclass
from typing import Any

import httpx

from .auth import get_secret

logger = logging.getLogger(__name__)

TIMEOUT = 10  # seconds


@dataclass
class BridgeError:
    message: str


def _client() -> httpx.Client:
    """Return an authenticated httpx client pointed at the bridge."""
    url = get_secret("BRIDGE_URL")
    key = get_secret("BRIDGE_API_KEY")
    return httpx.Client(
        base_url=url,
        headers={"Authorization": f"Bearer {key}"},
        timeout=TIMEOUT,
    )


def _get(path: str) -> dict | BridgeError:
    try:
        with _client() as c:
            r = c.get(path)
            r.raise_for_status()
            return r.json()
    except httpx.ConnectError:
        return BridgeError("Bridge is unreachable. Is the VPS running?")
    except httpx.HTTPStatusError as e:
        return BridgeError(f"Bridge returned {e.response.status_code}: {e.response.text}")
    except Exception as e:
        logger.exception("Unexpected bridge error")
        return BridgeError(str(e))


def _post(path: str, body: dict) -> dict | BridgeError:
    try:
        with _client() as c:
            r = c.post(path, json=body)
            r.raise_for_status()
            return r.json()
    except httpx.ConnectError:
        return BridgeError("Bridge is unreachable. Is the VPS running?")
    except httpx.HTTPStatusError as e:
        return BridgeError(f"Bridge returned {e.response.status_code}: {e.response.text}")
    except Exception as e:
        logger.exception("Unexpected bridge error")
        return BridgeError(str(e))


def _patch(path: str, body: dict) -> dict | BridgeError:
    try:
        with _client() as c:
            r = c.patch(path, json=body)
            r.raise_for_status()
            return r.json()
    except httpx.ConnectError:
        return BridgeError("Bridge is unreachable. Is the VPS running?")
    except httpx.HTTPStatusError as e:
        return BridgeError(f"Bridge returned {e.response.status_code}: {e.response.text}")
    except Exception as e:
        logger.exception("Unexpected bridge error")
        return BridgeError(str(e))


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

def register_user(whatsapp_number: str) -> dict | BridgeError:
    """Register a new user and trigger the first WhatsApp message."""
    return _post("/users/register", {"whatsapp_number": whatsapp_number})


def save_profile(user_id: str, profile: dict) -> dict | BridgeError:
    return _post("/users/profile", {"user_id": user_id, **profile})


def save_schedule(user_id: str, schedule: dict) -> dict | BridgeError:
    return _post("/users/schedule", {"user_id": user_id, **schedule})


def get_user_status(user_id: str) -> dict | BridgeError:
    return _get(f"/users/{user_id}/status")


def relink_whatsapp(user_id: str) -> dict | BridgeError:
    return _post("/users/relink-whatsapp", {"user_id": user_id})


# ---------------------------------------------------------------------------
# Memory
# ---------------------------------------------------------------------------

def get_vocab(user_id: str) -> dict | BridgeError:
    return _get(f"/memory/{user_id}/vocab")


def update_vocab_word(user_id: str, word_id: int, payload: dict) -> dict | BridgeError:
    return _patch(f"/memory/{user_id}/vocab/{word_id}", payload)


def get_raw_memory(user_id: str) -> dict | BridgeError:
    return _get(f"/memory/{user_id}/raw")


def update_raw_memory(user_id: str, payload: dict) -> dict | BridgeError:
    return _patch(f"/memory/{user_id}/raw", payload)


# ---------------------------------------------------------------------------
# Lessons
# ---------------------------------------------------------------------------

def get_lesson_plan(user_id: str) -> dict | BridgeError:
    return _get(f"/lessons/plan/{user_id}")


def update_lesson_plan(user_id: str, payload: dict) -> dict | BridgeError:
    return _patch(f"/lessons/plan/{user_id}", payload)


def generate_lesson_plan(user_id: str) -> dict | BridgeError:
    return _post("/lessons/generate-plan", {"user_id": user_id})


def trigger_lesson(user_id: str) -> dict | BridgeError:
    return _post(f"/lessons/trigger/{user_id}", {})


# ---------------------------------------------------------------------------
# Integrations
# ---------------------------------------------------------------------------

def get_google_auth_url() -> dict | BridgeError:
    return _get("/integrations/google/auth-url")


def get_google_status() -> dict | BridgeError:
    return _get("/integrations/google/status")
