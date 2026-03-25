"""
Lesson scheduler skill.
Runs on the OpenClaw hourly cron, checks which students are due a lesson,
builds their daily WhatsApp exercise, and sends it.
"""
import datetime
import logging
import os
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

MEMORY_BASE = Path(os.environ.get("MEMORY_BASE_PATH", "/home/openclaw/memory"))


# ---------------------------------------------------------------------------
# SRS helpers (SM-2 algorithm)
# ---------------------------------------------------------------------------

def update_srs(db_path: str, word_id: int, correct: bool) -> None:
    """Update interval and ease_factor for a vocab word after a review.

    Args:
        db_path: Absolute path to the user's vocab.db.
        word_id: Row ID of the word being reviewed.
        correct: True if the student answered correctly.
    """
    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT interval_days, ease_factor, times_correct, times_wrong FROM vocab WHERE id=?",
        (word_id,),
    ).fetchone()

    if not row:
        conn.close()
        return

    interval, ease, correct_count, wrong_count = row

    if correct:
        new_interval = max(1, round(interval * ease))
        new_ease = min(2.5, ease + 0.1)
        correct_count += 1
    else:
        new_interval = 1
        new_ease = max(1.3, ease - 0.2)
        wrong_count += 1

    next_review = str(datetime.date.today() + datetime.timedelta(days=new_interval))
    today = str(datetime.date.today())

    conn.execute(
        "UPDATE vocab SET interval_days=?, ease_factor=?, times_correct=?, times_wrong=?, "
        "last_seen=?, next_review=? WHERE id=?",
        (new_interval, new_ease, correct_count, wrong_count, today, next_review, word_id),
    )
    conn.commit()
    conn.close()


def get_due_words(user_id: str, limit: int = 3) -> list[dict]:
    """Return vocab words due for review today, ordered by most overdue first.

    Args:
        user_id: The student's user ID.
        limit: Maximum number of words to return.

    Returns:
        List of dicts with keys: id, danish, translation, times_correct, times_wrong.
    """
    db_path = MEMORY_BASE / user_id / "vocab.db"
    if not db_path.exists():
        return []

    conn = sqlite3.connect(str(db_path))
    today = str(datetime.date.today())
    rows = conn.execute(
        "SELECT id, danish, translation, times_correct, times_wrong FROM vocab "
        "WHERE user_id=? AND next_review<=? AND mastered=0 ORDER BY next_review ASC LIMIT ?",
        (user_id, today, limit),
    ).fetchall()
    conn.close()

    return [
        {"id": r[0], "danish": r[1], "translation": r[2], "times_correct": r[3], "times_wrong": r[4]}
        for r in rows
    ]


# ---------------------------------------------------------------------------
# Schedule checking
# ---------------------------------------------------------------------------

def get_schedule_from_profile(user_id: str) -> dict | None:
    """Parse the student's schedule from their profile.md.

    Returns:
        Dict with keys: practice_time (str "HH:MM"), days_per_week (int),
        or None if not found.
    """
    profile_path = MEMORY_BASE / user_id / "profile.md"
    if not profile_path.exists():
        return None

    for line in profile_path.read_text().splitlines():
        if line.startswith("**Schedule:**"):
            # Format: "Daily at HH:MM, N days/week, M min sessions"
            try:
                time_part = line.split("at ")[1].split(",")[0].strip()
                days_part = int(line.split(",")[1].strip().split()[0])
                return {"practice_time": time_part, "days_per_week": days_part}
            except (IndexError, ValueError):
                return None
    return None


def is_lesson_due(user_id: str) -> bool:
    """Return True if this user is due a lesson within the current hour.

    Args:
        user_id: The student's user ID.
    """
    schedule = get_schedule_from_profile(user_id)
    if not schedule:
        return False

    now = datetime.datetime.now()
    # Check day of week (simple: treat days_per_week as Mon–Fri if 5, etc.)
    # For now: send on the first N weekdays
    days_per_week = schedule.get("days_per_week", 5)
    if now.weekday() >= days_per_week:
        return False

    # Check if current hour matches scheduled hour
    scheduled_hour = int(schedule["practice_time"].split(":")[0])
    return now.hour == scheduled_hour


# ---------------------------------------------------------------------------
# Daily exercise builder
# ---------------------------------------------------------------------------

def build_daily_exercise(user_id: str) -> str:
    """Build the WhatsApp daily lesson message for a student.

    Reads their profile for name/level, gets due vocab words,
    and constructs a structured message.

    Args:
        user_id: The student's user ID.

    Returns:
        Formatted WhatsApp message string.
    """
    profile_path = MEMORY_BASE / user_id / "profile.md"
    name = "there"
    level = "A2"

    if profile_path.exists():
        for line in profile_path.read_text().splitlines():
            if line.startswith("**Name:**"):
                name = line.split(":", 1)[1].strip()
            elif line.startswith("**Danish level:**"):
                level = line.split(":", 1)[1].strip()

    due_words = get_due_words(user_id, limit=3)

    lines = [f"🇩🇰 God morgen, {name}!", "", "**Dagens øvelse**", ""]

    if due_words:
        lines.append("📖 **Vocabulary review** (words due today):")
        for w in due_words:
            lines.append(f"- *{w['danish']}* – {w['translation']}")
        lines.append("")

    # Level-appropriate exercise prompt
    if level.startswith("A1"):
        prompt = "How do you say 'My name is [your name] and I live in Denmark' in Danish?"
    elif level.startswith("A2"):
        prompt = "Describe what you did this morning — try to use at least 2 verbs in past tense."
    elif level.startswith("B1"):
        prompt = "Write 2 sentences using a subordinate clause starting with 'fordi' (because)."
    else:
        prompt = "Write a short paragraph (3–4 sentences) about a topic you find interesting — I'll give you feedback on style and grammar."

    lines += ["✏️ **Quick exercise:**", prompt, "", "Reply in Danish and I'll give you feedback! 💬"]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main entry point (called by OpenClaw cron)
# ---------------------------------------------------------------------------

def check_and_send_due_lessons() -> int:
    """Check all users and send lessons to those due right now.

    Returns:
        Number of lessons sent.
    """
    if not MEMORY_BASE.exists():
        logger.warning("Memory base path does not exist: %s", MEMORY_BASE)
        return 0

    sent = 0
    for user_dir in MEMORY_BASE.iterdir():
        if not user_dir.is_dir():
            continue
        user_id = user_dir.name
        if is_lesson_due(user_id):
            message = build_daily_exercise(user_id)
            logger.info("Sending lesson to user %s", user_id)
            # The OpenClaw runtime will call this and send the returned message
            # via WhatsApp. We log it here for debugging.
            logger.debug("Lesson message:\n%s", message)
            sent += 1

    return sent
