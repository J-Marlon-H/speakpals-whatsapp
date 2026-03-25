"""User-facing strings and option lists used across all pages."""

APP_TITLE = "SpeakPals"
APP_ICON = "🦜"

NATIVE_LANGUAGES = [
    "English", "German", "Arabic", "Chinese",
    "Spanish", "Portuguese", "French", "Other",
]

DANISH_LEVELS = [
    "A1 – Complete beginner",
    "A2 – Elementary",
    "B1 – Intermediate",
    "B2 – Upper intermediate",
    "C1 – Advanced",
]

LEARNING_GOALS = [
    "Pass Prøve i Dansk 1",
    "Pass Prøve i Dansk 2",
    "Pass Prøve i Dansk 3",
    "Pass Studieprøven",
    "Everyday conversation",
    "Work Danish",
    "General improvement",
]

CHALLENGES = [
    "Pronunciation", "Grammar", "Vocabulary",
    "Listening", "Reading", "Writing",
]

SESSION_LENGTHS = ["5 min", "10 min", "15 min", "20 min"]

BRIDGE_UNREACHABLE_MSG = (
    "⚠️ Cannot reach the VPS bridge. "
    "Make sure the Droplet is running and BRIDGE_URL is set in your secrets."
)
