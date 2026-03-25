---
name: speakpals-google-suite
description: Google Calendar and Gmail integration via the gog ClawHub plugin. Use when the student asks about their schedule, when checking for free time, or when using email context for lesson exercises.
---

# SpeakPals Google Suite Integration

## Requires
- ClawHub `gog` plugin installed: `clawhub install gog`
- First-time OAuth completed: `node scripts/gog_auth.js` (HUMAN DEPENDENCY — see HUMAN_SETUP_INSTRUCTIONS Part 6)
- Token stored at `/home/openclaw/config/google_token.json`

## Use cases

### Calendar
- "What does [student] have this week?" → read Google Calendar events
- "Is [student] free tomorrow morning?" → check free/busy for the next lesson slot
- "Schedule a lesson reminder for [student] at [time]" → create a calendar event

### Gmail (read-only)
- "Read [student]'s recent emails for Danish practice context" → summarise relevant emails (e.g. work emails in Danish) and turn them into lesson material
- Never send emails on behalf of the student

## Configuration (in openclaw.yaml)
```yaml
plugins:
  gog:
    enabled: true
    scopes:
      calendar: read_write
      gmail: readonly
    default_calendar: primary
    timezone: Europe/Copenhagen
```

## Notes
- Timezone is always Europe/Copenhagen for Danish students
- Only access calendar/email when the student explicitly asks or when scheduling a lesson
- Never read personal/private emails unless student requests it for practice material
