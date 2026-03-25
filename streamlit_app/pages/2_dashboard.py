"""Dashboard – streak, next lesson, last session, vocab due today."""
import streamlit as st

from utils.bridge_client import BridgeError, get_user_status, trigger_lesson
from utils.constants import APP_ICON, BRIDGE_UNREACHABLE_MSG

st.set_page_config(page_title="Dashboard – SpeakPals", page_icon=APP_ICON)

if not st.session_state.get("user_id"):
    st.warning("Please complete onboarding first.")
    st.page_link("pages/1_onboarding.py", label="→ Go to onboarding")
    st.stop()

user_id = st.session_state.user_id

st.title(f"{APP_ICON} Dashboard")

with st.spinner("Loading your progress…"):
    status = get_user_status(user_id)

if isinstance(status, BridgeError):
    st.error(BRIDGE_UNREACHABLE_MSG)
    st.caption(status.message)
    st.stop()

data = status.get("data", {})

# ---------------------------------------------------------------------------
# Top metrics row
# ---------------------------------------------------------------------------
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("🔥 Practice streak", f"{data.get('streak_days', 0)} days")
with col2:
    st.metric("📅 Next lesson", data.get("next_lesson", "Not scheduled"))
with col3:
    st.metric("📊 Words learned", data.get("words_learned", 0))

st.divider()

# ---------------------------------------------------------------------------
# Last session summary
# ---------------------------------------------------------------------------
st.subheader("Last session")
last = data.get("last_session")
if last:
    st.write(f"**{last.get('date', '—')}** · {last.get('topic', '—')}")
    c1, c2 = st.columns(2)
    c1.metric("Correct", last.get("correct", 0))
    c2.metric("Errors", last.get("errors", 0))
    if last.get("notes"):
        st.caption(last["notes"])
else:
    st.caption("No sessions completed yet.")

st.divider()

# ---------------------------------------------------------------------------
# Vocab due today
# ---------------------------------------------------------------------------
st.subheader("📖 Words due for review today")
vocab_due = data.get("vocab_due_today", [])
if vocab_due:
    for word in vocab_due[:3]:
        st.write(f"- **{word['danish']}** — {word['translation']}")
else:
    st.caption("No words due today. 🎉")

st.divider()

# ---------------------------------------------------------------------------
# Quick action
# ---------------------------------------------------------------------------
if st.button("Send me a lesson now ▶", type="primary"):
    with st.spinner("Sending lesson to WhatsApp…"):
        result = trigger_lesson(user_id)
    if isinstance(result, BridgeError):
        st.error(BRIDGE_UNREACHABLE_MSG)
        st.caption(result.message)
    else:
        st.success("Lesson sent! Check your WhatsApp. 📱")
