"""Lesson plan and lesson trigger routes."""
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from openclaw_client import run_command

router = APIRouter()

MEMORY_BASE = Path(os.environ.get("MEMORY_BASE_PATH", "/home/openclaw/memory"))


class GeneratePlanRequest(BaseModel):
    user_id: str


class PlanUpdate(BaseModel):
    week: int
    raw: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/plan/{user_id}")
def get_lesson_plan(user_id: str) -> dict:
    """Read the current lesson plan from lesson_plan.md."""
    plan_path = MEMORY_BASE / user_id / "lesson_plan.md"
    if not plan_path.exists():
        return {"status": "ok", "data": {"weeks": []}}

    raw = plan_path.read_text()
    # Parse week blocks (simple: each ## Week N section)
    weeks = []
    current: dict | None = None
    for line in raw.splitlines():
        if line.startswith("## Week"):
            if current:
                weeks.append(current)
            parts = line[3:].split("—", 1)
            current = {
                "week": len(weeks) + 1,
                "focus": parts[1].strip() if len(parts) > 1 else "",
                "topics": "",
                "grammar": "",
                "vocab_count": 0,
                "raw": line,
            }
        elif current:
            current["raw"] += "\n" + line
            if line.startswith("- Focus:"):
                current["topics"] = line[8:].strip()
            elif line.startswith("- Grammar:"):
                current["grammar"] = line[10:].strip()
            elif "Target vocab:" in line:
                try:
                    current["vocab_count"] = int(line.split(":")[1].split()[0])
                except (ValueError, IndexError):
                    pass

    if current:
        weeks.append(current)

    return {"status": "ok", "data": {"weeks": weeks, "raw": raw}}


@router.patch("/plan/{user_id}")
def update_lesson_plan(user_id: str, payload: PlanUpdate) -> dict:
    """Overwrite a single week block in lesson_plan.md."""
    plan_path = MEMORY_BASE / user_id / "lesson_plan.md"
    if not plan_path.exists():
        raise HTTPException(status_code=404, detail="No lesson plan found")

    raw = plan_path.read_text()
    lines = raw.splitlines()
    new_lines = []
    week_num = 0
    inside_target = False

    for line in lines:
        if line.startswith("## Week"):
            week_num += 1
            if week_num == payload.week:
                inside_target = True
                new_lines.append(payload.raw)
                continue
            else:
                inside_target = False
        if not inside_target:
            new_lines.append(line)

    plan_path.write_text("\n".join(new_lines) + "\n")
    return {"status": "ok", "data": {}}


@router.post("/generate-plan")
def generate_plan(req: GeneratePlanRequest) -> dict:
    """Ask OpenClaw to generate a 4-week lesson plan for this user."""
    try:
        run_command(
            f"Generate a 4-week Danish lesson plan for user {req.user_id} "
            "based on their profile.md. Save it to their lesson_plan.md."
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"OpenClaw unreachable: {e}")
    return {"status": "ok", "data": {}}


@router.post("/trigger/{user_id}")
def trigger_lesson(user_id: str) -> dict:
    """Send today's lesson exercise to the user on WhatsApp now."""
    plan_path = MEMORY_BASE / user_id / "lesson_plan.md"
    if not (MEMORY_BASE / user_id).exists():
        raise HTTPException(status_code=404, detail="User not found")
    try:
        run_command(
            f"Send today's Danish lesson exercise to user {user_id} on WhatsApp now."
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"OpenClaw unreachable: {e}")
    return {"status": "ok", "data": {}}
