"""Lesson plan – view and edit the current 4-week plan."""
import streamlit as st

from utils.bridge_client import (
    BridgeError, get_lesson_plan, update_lesson_plan, generate_lesson_plan,
)
from utils.constants import APP_ICON, BRIDGE_UNREACHABLE_MSG

st.set_page_config(page_title="Lesson Plan – SpeakPals", page_icon=APP_ICON)

if not st.session_state.get("user_id"):
    st.warning("Please complete onboarding first.")
    st.stop()

user_id = st.session_state.user_id

st.title("📅 Lesson Plan")

with st.spinner("Loading your plan…"):
    result = get_lesson_plan(user_id)

if isinstance(result, BridgeError):
    st.error(BRIDGE_UNREACHABLE_MSG)
    st.caption(result.message)
    st.stop()

plan = result.get("data", {})
weeks = plan.get("weeks", [])

# ---------------------------------------------------------------------------
# Week-by-week view
# ---------------------------------------------------------------------------
if weeks:
    for week in weeks:
        with st.expander(f"Week {week['week']} — {week.get('focus', '')}", expanded=False):
            st.write(f"**Topics:** {week.get('topics', '—')}")
            st.write(f"**Grammar:** {week.get('grammar', '—')}")
            st.write(f"**Target vocabulary:** {week.get('vocab_count', 0)} words")

            if st.toggle("Edit this week", key=f"edit_week_{week['week']}"):
                new_content = st.text_area(
                    "Edit week content (markdown)",
                    value=week.get("raw", ""),
                    key=f"content_week_{week['week']}",
                )
                if st.button("Save", key=f"save_week_{week['week']}"):
                    with st.spinner("Saving…"):
                        r = update_lesson_plan(user_id, {"week": week["week"], "raw": new_content})
                    if isinstance(r, BridgeError):
                        st.error(r.message)
                    else:
                        st.success("Saved.")
                        st.rerun()
else:
    st.info("No lesson plan yet. Generate one below.")

st.divider()

# ---------------------------------------------------------------------------
# Regenerate plan
# ---------------------------------------------------------------------------
st.subheader("Regenerate full plan")
st.caption("This will replace your current plan with a new AI-generated one.")

if st.button("🔄 Regenerate plan"):
    confirmed = st.checkbox("Yes, I want to replace my current plan")
    if confirmed:
        with st.spinner("Asking your tutor to build a new plan… (this may take a moment)"):
            r = generate_lesson_plan(user_id)
        if isinstance(r, BridgeError):
            st.error(BRIDGE_UNREACHABLE_MSG)
            st.caption(r.message)
        else:
            st.success("New plan generated! Refresh the page to see it.")
