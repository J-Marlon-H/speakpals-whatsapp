"""User registration and profile routes."""
import logging
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from openclaw_client import run_command

logger = logging.getLogger(__name__)
router = APIRouter()

MEMORY_BASE = Path(os.environ.get("MEMORY_BASE_PATH", "/home/openclaw/memory"))


def _user_dir(user_id: str) -> Path:
    return MEMORY_BASE / user_id


def _ensure_user_dir(user_id: str) -> Path:
    d = _user_dir(user_id)
    d.mkdir(parents=True, exist_ok=True)
    return d


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    whatsapp_number: str


class ProfileRequest(BaseModel):
    user_id: str
    native_language: str
    danish_level: str
    goal: str
    challenges: list[str]


class RelinkRequest(BaseModel):
    user_id: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/register")
def register_user(req: RegisterRequest) -> dict:
    """Create a new user record and send a WhatsApp welcome message."""
    user_id = str(uuid.uuid4())[:8]
    user_dir = _ensure_user_dir(user_id)

    # Write a minimal profile stub so the agent has context
    profile_path = user_dir / "profile.md"
    profile_path.write_text(
        f"# Student Profile\n\n**WhatsApp:** {req.whatsapp_number}\n**Started:** "
        + str(__import__("datetime").date.today())
        + "\n"
    )

    try:
        run_command(
            f"Send a welcome WhatsApp message to {req.whatsapp_number} and begin onboarding. "
            f"Their user_id is {user_id}."
        )
    except Exception as e:
        logger.warning("OpenClaw unreachable during register: %s", e)
        # Don't fail registration if OpenClaw is temporarily down

    return {"status": "ok", "data": {"user_id": user_id}}


@router.post("/profile")
def save_profile(req: ProfileRequest) -> dict:
    """Persist language profile to profile.md."""
    user_dir = _ensure_user_dir(req.user_id)
    profile_path = user_dir / "profile.md"

    # Read existing to preserve fields we're not overwriting
    existing = profile_path.read_text() if profile_path.exists() else "# Student Profile\n\n"

    challenges_str = ", ".join(req.challenges) if req.challenges else "—"
    additions = (
        f"**Native language:** {req.native_language}\n"
        f"**Danish level:** {req.danish_level}\n"
        f"**Goal:** {req.goal}\n"
        f"**Challenges:** {challenges_str}\n"
    )

    # Replace or append the relevant lines
    profile_path.write_text(existing.strip() + "\n" + additions)
    return {"status": "ok", "data": {}}


@router.get("/{user_id}/status")
def get_user_status(user_id: str) -> dict:
    """Return streak, next lesson, last session summary, and vocab due today."""
    user_dir = _user_dir(user_id)
    if not user_dir.exists():
        raise HTTPException(status_code=404, detail="User not found")

    # Read lesson history for streak / last session (simple parse)
    history_path = user_dir / "lesson_history.md"
    last_session = None
    streak_days = 0

    if history_path.exists():
        lines = history_path.read_text().splitlines()
        # Last session = last ## heading block
        for line in reversed(lines):
            if line.startswith("## "):
                last_session = {"date": line[3:], "topic": "—", "correct": 0, "errors": 0}
                break

    # Read vocab DB for words due today
    import sqlite3, datetime
    vocab_due = []
    vocab_db = user_dir / "vocab.db"
    if vocab_db.exists():
        conn = sqlite3.connect(str(vocab_db))
        today = str(datetime.date.today())
        rows = conn.execute(
            "SELECT danish, translation FROM vocab WHERE next_review <= ? AND mastered=0 LIMIT 3",
            (today,),
        ).fetchall()
        conn.close()
        vocab_due = [{"danish": r[0], "translation": r[1]} for r in rows]

    return {
        "status": "ok",
        "data": {
            "streak_days": streak_days,
            "next_lesson": "—",
            "words_learned": 0,
            "last_session": last_session,
            "vocab_due_today": vocab_due,
        },
    }


@router.post("/relink-whatsapp")
def relink_whatsapp(req: RelinkRequest) -> dict:
    """Trigger a new WhatsApp QR pairing flow via OpenClaw."""
    try:
        run_command("Re-trigger the WhatsApp QR pairing flow.")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"OpenClaw unreachable: {e}")
    return {"status": "ok", "data": {}}
