"""
Language tutor helper logic.
Called by the OpenClaw skill runtime to post-process tutor responses
and update lesson_history.md after each session.
"""
import datetime
import logging
import os
import re
from pathlib import Path

logger = logging.getLogger(__name__)

MEMORY_BASE = Path(os.environ.get("MEMORY_BASE_PATH", "/home/openclaw/memory"))


def append_lesson_history(user_id: str, topic: str, notes: str = "") -> None:
    """Append a session summary to the user's lesson_history.md.

    Args:
        user_id: The student's user ID.
        topic: Short description of what was practiced (e.g. "vocabulary review, past tense").
        notes: Any notable observations (errors made, breakthroughs, etc.).
    """
    history_path = MEMORY_BASE / user_id / "lesson_history.md"

    today = str(datetime.date.today())
    entry = f"\n## {today}\n- Topic: {topic}\n"
    if notes:
        entry += f"- Notes: {notes}\n"

    if not history_path.exists():
        history_path.write_text("# Lesson History\n" + entry)
    else:
        with history_path.open("a") as f:
            f.write(entry)

    logger.info("Lesson history updated for user %s", user_id)


def count_errors_in_response(tutor_response: str) -> int:
    """Count how many corrections were made in a tutor response.

    Corrections are marked with strikethrough: ~~error~~ → **fix**

    Args:
        tutor_response: The raw tutor message text.

    Returns:
        Number of corrections found.
    """
    return len(re.findall(r"~~.+?~~", tutor_response))


def extract_vocab_from_exercise(exercise_text: str) -> list[dict]:
    """Parse vocab items from a lesson exercise message.

    Looks for lines matching: *danish* – translation

    Args:
        exercise_text: The raw exercise message from the tutor.

    Returns:
        List of dicts with keys: danish, translation.
    """
    pattern = re.compile(r"\*(.+?)\*\s*[–-]\s*(.+)")
    vocab = []
    for match in pattern.finditer(exercise_text):
        vocab.append({
            "danish": match.group(1).strip(),
            "translation": match.group(2).strip(),
        })
    return vocab


def add_vocab_to_db(user_id: str, vocab_items: list[dict]) -> int:
    """Insert new vocab items into the user's SQLite vocab.db.

    Skips items that already exist (same Danish word).

    Args:
        user_id: The student's user ID.
        vocab_items: List of dicts with keys: danish, translation.

    Returns:
        Number of new words inserted.
    """
    import sqlite3

    db_path = MEMORY_BASE / user_id / "vocab.db"
    if not db_path.exists():
        logger.warning("vocab.db not found for user %s — skipping vocab insert", user_id)
        return 0

    conn = sqlite3.connect(str(db_path))
    inserted = 0
    today = str(datetime.date.today())

    for item in vocab_items:
        existing = conn.execute(
            "SELECT id FROM vocab WHERE user_id=? AND danish=?", (user_id, item["danish"])
        ).fetchone()
        if not existing:
            conn.execute(
                "INSERT INTO vocab (user_id, danish, translation, last_seen, next_review) VALUES (?,?,?,?,?)",
                (user_id, item["danish"], item["translation"], today, today),
            )
            inserted += 1

    conn.commit()
    conn.close()
    logger.info("Inserted %d new vocab words for user %s", inserted, user_id)
    return inserted
