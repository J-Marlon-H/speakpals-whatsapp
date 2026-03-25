"""
Onboarding wizard – 3 steps:
  1. WhatsApp number
  2. Language profile
  3. Schedule
"""
import streamlit as st

from utils.bridge_client import (
    BridgeError, register_user, save_profile,
    save_schedule, generate_lesson_plan,
)
from utils.constants import (
    APP_ICON, NATIVE_LANGUAGES, DANISH_LEVELS,
    LEARNING_GOALS, CHALLENGES, SESSION_LENGTHS,
    BRIDGE_UNREACHABLE_MSG,
)

st.set_page_config(page_title="Onboarding – SpeakPals", page_icon=APP_ICON)
st.title(f"{APP_ICON} Set up SpeakPals")

# Session state defaults
for key, default in [("step", 1), ("ob_user_id", None), ("ob_wa_number", "")]:
    if key not in st.session_state:
        st.session_state[key] = default

# ---------------------------------------------------------------------------
# Progress indicator
# ---------------------------------------------------------------------------
steps = ["WhatsApp number", "Language profile", "Schedule"]
cols = st.columns(3)
for i, (col, label) in enumerate(zip(cols, steps), start=1):
    with col:
        if i < st.session_state.step:
            st.success(f"✓ {label}")
        elif i == st.session_state.step:
            st.info(f"→ {label}")
        else:
            st.caption(label)

st.divider()

# ---------------------------------------------------------------------------
# Step 1 – WhatsApp number
# ---------------------------------------------------------------------------
if st.session_state.step == 1:
    st.subheader("Step 1 – Your WhatsApp number")
    st.write("Enter the number you want to receive Danish lessons on.")

    number = st.text_input(
        "WhatsApp number (E.164 format)",
        placeholder="+4512345678",
        value=st.session_state.ob_wa_number,
    )

    if st.button("Send me a confirmation message", type="primary"):
        if not number.startswith("+") or len(number) < 8:
            st.error("Please enter a valid number in E.164 format, e.g. +4512345678")
        else:
            with st.spinner("Registering your number…"):
                result = register_user(number)
            if isinstance(result, BridgeError):
                st.error(BRIDGE_UNREACHABLE_MSG)
                st.caption(result.message)
            else:
                st.session_state.ob_user_id = result["data"]["user_id"]
                st.session_state.ob_wa_number = number
                st.success(
                    "We've sent you a WhatsApp message. Reply to confirm, "
                    "then click Continue below."
                )
                if st.button("Continue →"):
                    st.session_state.step = 2
                    st.rerun()

# ---------------------------------------------------------------------------
# Step 2 – Language profile
# ---------------------------------------------------------------------------
elif st.session_state.step == 2:
    st.subheader("Step 2 – Your language profile")

    native_lang = st.selectbox("Your native language", NATIVE_LANGUAGES)
    danish_level = st.selectbox("Your current Danish level", DANISH_LEVELS)
    goal = st.selectbox("Your learning goal", LEARNING_GOALS)
    challenges = st.multiselect("Your biggest challenges (pick all that apply)", CHALLENGES)

    if st.button("Save profile →", type="primary"):
        with st.spinner("Saving…"):
            result = save_profile(
                st.session_state.ob_user_id,
                {
                    "native_language": native_lang,
                    "danish_level": danish_level,
                    "goal": goal,
                    "challenges": challenges,
                },
            )
        if isinstance(result, BridgeError):
            st.error(BRIDGE_UNREACHABLE_MSG)
            st.caption(result.message)
        else:
            st.session_state.step = 3
            st.rerun()

# ---------------------------------------------------------------------------
# Step 3 – Schedule
# ---------------------------------------------------------------------------
elif st.session_state.step == 3:
    st.subheader("Step 3 – Your practice schedule")

    import datetime
    practice_time = st.time_input(
        "Preferred daily practice time",
        value=datetime.time(8, 0),
    )
    days_per_week = st.slider("Days per week", min_value=1, max_value=7, value=5)
    session_length = st.selectbox("Session length", SESSION_LENGTHS, index=1)

    if st.button("Finish setup 🎉", type="primary"):
        with st.spinner("Saving schedule and generating your first lesson plan…"):
            result = save_schedule(
                st.session_state.ob_user_id,
                {
                    "practice_time": practice_time.strftime("%H:%M"),
                    "days_per_week": days_per_week,
                    "session_length": session_length,
                },
            )
            if not isinstance(result, BridgeError):
                generate_lesson_plan(st.session_state.ob_user_id)

        if isinstance(result, BridgeError):
            st.error(BRIDGE_UNREACHABLE_MSG)
            st.caption(result.message)
        else:
            # Promote to full session
            st.session_state.user_id = st.session_state.ob_user_id
            st.session_state.whatsapp_number = st.session_state.ob_wa_number
            st.success("You're all set! Your Danish tutor will message you at the scheduled time.")
            st.page_link("pages/2_dashboard.py", label="→ Go to Dashboard")
