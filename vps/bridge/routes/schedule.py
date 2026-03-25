"""Schedule save route."""
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

MEMORY_BASE = Path(os.environ.get("MEMORY_BASE_PATH", "/home/openclaw/memory"))


class ScheduleRequest(BaseModel):
    user_id: str
    practice_time: str   # "HH:MM"
    days_per_week: int
    session_length: str  # e.g. "10 min"


@router.post("/schedule")
def save_schedule(req: ScheduleRequest) -> dict:
    """Append/update schedule fields in the user's profile.md."""
    user_dir = MEMORY_BASE / req.user_id
    if not user_dir.exists():
        raise HTTPException(status_code=404, detail="User not found")

    profile_path = user_dir / "profile.md"
    existing = profile_path.read_text() if profile_path.exists() else "# Student Profile\n\n"

    schedule_line = (
        f"**Schedule:** Daily at {req.practice_time}, "
        f"{req.days_per_week} days/week, {req.session_length} sessions\n"
    )

    # Remove old schedule line if present, then append updated one
    lines = [l for l in existing.splitlines() if not l.startswith("**Schedule:**")]
    lines.append(schedule_line.strip())
    profile_path.write_text("\n".join(lines) + "\n")

    return {"status": "ok", "data": {}}
