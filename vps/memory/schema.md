# Memory Schema

Each student gets a folder at `/home/openclaw/memory/{user_id}/`.

---

## Files

### `profile.md`
Human-readable student profile. Read by the language-tutor skill on every message.

```markdown
# Student Profile

**Name:** Marlon
**WhatsApp:** +45...
**Native language:** English
**Danish level:** A2
**Goal:** Pass Prøve i Dansk 2
**Challenges:** Pronunciation, Grammar
**Schedule:** Daily at 08:00, 5 days/week, 10 min sessions
**Timezone:** Europe/Copenhagen
**Started:** 2026-03-25
```

---

### `lesson_plan.md`
Current 4-week lesson plan. Updated by the lesson-scheduler skill.

```markdown
# Lesson Plan

**Generated:** 2026-03-25
**Level:** A2
**Goal:** Prøve i Dansk 2

## Week 1 — Everyday Vocabulary
- Focus: greetings, numbers, telling time
- Grammar: definite/indefinite articles
- Target vocab: 20 words

## Week 2 — ...
```

---

### `lesson_history.md`
Append-only log of completed sessions.

```markdown
# Lesson History

## 2026-03-25
- Exercise type: vocabulary review
- Words practiced: 5
- Correct: 4 / Wrong: 1
- Notes: Struggled with gendered nouns
```

---

### `vocab.db`
SQLite database for spaced repetition (SRS) vocabulary tracking.

```sql
CREATE TABLE vocab (
    id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL,
    danish TEXT NOT NULL,
    translation TEXT NOT NULL,
    last_seen DATE,
    next_review DATE,
    interval_days INTEGER DEFAULT 1,
    ease_factor REAL DEFAULT 2.5,
    times_correct INTEGER DEFAULT 0,
    times_wrong INTEGER DEFAULT 0,
    mastered BOOLEAN DEFAULT 0
);
```

**SRS logic (SM-2 algorithm):**
- After correct answer: `interval = interval * ease_factor`, `ease_factor += 0.1` (max 2.5)
- After wrong answer: `interval = 1`, `ease_factor -= 0.2` (min 1.3)
- `next_review = today + interval_days`
