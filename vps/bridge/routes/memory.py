"""Memory read/write routes (raw .md files + SQLite vocab)."""
import os
import sqlite3
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

MEMORY_BASE = Path(os.environ.get("MEMORY_BASE_PATH", "/home/openclaw/memory"))
MEMORY_FILES = ["profile.md", "lesson_plan.md", "lesson_history.md"]


def _user_dir(user_id: str) -> Path:
    d = MEMORY_BASE / user_id
    if not d.exists():
        raise HTTPException(status_code=404, detail="User not found")
    return d


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class RawMemoryUpdate(BaseModel):
    # keys are filenames e.g. "profile.md", values are new markdown content
    __root__: dict[str, str]

    def items(self):
        return self.__root__.items()


class VocabUpdate(BaseModel):
    mastered: bool | None = None
    times_correct: int | None = None
    times_wrong: int | None = None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/{user_id}/raw")
def get_raw_memory(user_id: str) -> dict:
    """Return all memory .md files as a dict keyed by filename."""
    user_dir = _user_dir(user_id)
    result = {}
    for filename in MEMORY_FILES:
        path = user_dir / filename
        result[filename] = path.read_text() if path.exists() else ""
    return {"status": "ok", "data": result}


@router.patch("/{user_id}/raw")
def update_raw_memory(user_id: str, payload: dict) -> dict:
    """Overwrite one or more memory .md files."""
    user_dir = _user_dir(user_id)
    for filename, content in payload.items():
        if filename not in MEMORY_FILES:
            raise HTTPException(status_code=400, detail=f"Unknown memory file: {filename}")
        (user_dir / filename).write_text(content)
    return {"status": "ok", "data": {}}


@router.get("/{user_id}/vocab")
def get_vocab(user_id: str) -> dict:
    """Return all vocab records from SQLite."""
    user_dir = _user_dir(user_id)
    db_path = user_dir / "vocab.db"
    if not db_path.exists():
        return {"status": "ok", "data": {"words": []}}

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, danish, translation, last_seen, next_review, "
        "times_correct, times_wrong, mastered FROM vocab WHERE user_id=?",
        (user_id,),
    ).fetchall()
    conn.close()

    words = [dict(r) for r in rows]
    return {"status": "ok", "data": {"words": words}}


@router.patch("/{user_id}/vocab/{word_id}")
def update_vocab_word(user_id: str, word_id: int, payload: VocabUpdate) -> dict:
    """Update a single vocab record (e.g. mark as mastered)."""
    user_dir = _user_dir(user_id)
    db_path = user_dir / "vocab.db"
    if not db_path.exists():
        raise HTTPException(status_code=404, detail="Vocab DB not found")

    conn = sqlite3.connect(str(db_path))
    updates = {k: v for k, v in payload.dict().items() if v is not None}
    if not updates:
        conn.close()
        return {"status": "ok", "data": {}}

    set_clause = ", ".join(f"{k}=?" for k in updates)
    conn.execute(
        f"UPDATE vocab SET {set_clause} WHERE id=? AND user_id=?",
        (*updates.values(), word_id, user_id),
    )
    conn.commit()
    conn.close()
    return {"status": "ok", "data": {}}
