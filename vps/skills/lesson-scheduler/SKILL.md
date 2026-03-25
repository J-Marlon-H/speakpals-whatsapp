---
name: speakpals-lesson-scheduler
description: Daily lesson scheduler. Use when the cron fires (every hour) to check which students are due a lesson and send their daily exercise via WhatsApp.
---

# SpeakPals Lesson Scheduler

## Trigger
- OpenClaw hourly cron: `"check and send any due lessons"`
- Direct command: `"Send today's lesson exercise to user {user_id} on WhatsApp now"`

## On cron trigger
1. Call `scheduler.check_and_send_due_lessons()` to get the list of users due a lesson
2. For each due user:
   a. Call `scheduler.build_daily_exercise(user_id)` to get their message
   b. Look up their WhatsApp number from `profile.md`
   c. Send the message to that WhatsApp number

## On direct trigger (user clicked "Send me a lesson now" in Streamlit)
1. Call `scheduler.build_daily_exercise(user_id)` for the specified user
2. Look up their WhatsApp number from `profile.md`
3. Send the message immediately, regardless of schedule

## Daily message format
```
🇩🇰 God morgen, [Name]!

**Dagens øvelse**

📖 **Vocabulary review** (words due today):
- *at arbejde* – to work
- *mødet* – the meeting
- *forsinket* – late/delayed

✏️ **Quick exercise:**
[Level-appropriate prompt]

Reply in Danish and I'll give you feedback! 💬
```

## After sending
- Append a session log entry to `lesson_history.md` via `tutor.append_lesson_history()`
- Do NOT send more than one lesson per user per scheduled time slot
