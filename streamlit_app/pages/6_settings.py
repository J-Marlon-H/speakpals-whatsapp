"""Settings – schedule, goals, integrations, danger zone."""
import datetime
import streamlit as st

from utils.bridge_client import (
    BridgeError, save_profile, save_schedule,
    get_google_auth_url, get_google_status, relink_whatsapp, update_raw_memory,
)
from utils.constants import (
    APP_ICON, NATIVE_LANGUAGES, DANISH_LEVELS, LEARNING_GOALS,
    CHALLENGES, SESSION_LENGTHS, BRIDGE_UNREACHABLE_MSG,
)

st.set_page_config(page_title="Settings – SpeakPals", page_icon=APP_ICON)

if not st.session_state.get("user_id"):
    st.warning("Please complete onboarding first.")
    st.stop()

user_id = st.session_state.user_id

st.title("⚙️ Settings")

# ---------------------------------------------------------------------------
# Schedule
# ---------------------------------------------------------------------------
st.subheader("Schedule")
with st.form("schedule_form"):
    practice_time = st.time_input("Daily practice time", value=datetime.time(8, 0))
    days_per_week = st.slider("Days per week", 1, 7, 5)
    session_length = st.selectbox("Session length", SESSION_LENGTHS, index=1)
    submitted = st.form_submit_button("Save schedule")

if submitted:
    with st.spinner("Saving…"):
        r = save_schedule(user_id, {
            "practice_time": practice_time.strftime("%H:%M"),
            "days_per_week": days_per_week,
            "session_length": session_length,
        })
    if isinstance(r, BridgeError):
        st.error(BRIDGE_UNREACHABLE_MSG)
    else:
        st.success("Schedule updated.")

st.divider()

# ---------------------------------------------------------------------------
# Language goals
# ---------------------------------------------------------------------------
st.subheader("Language goals")
with st.form("profile_form"):
    native_lang = st.selectbox("Native language", NATIVE_LANGUAGES)
    danish_level = st.selectbox("Current Danish level", DANISH_LEVELS)
    goal = st.selectbox("Learning goal", LEARNING_GOALS)
    challenges = st.multiselect("Challenges", CHALLENGES)
    submitted_profile = st.form_submit_button("Save goals")

if submitted_profile:
    with st.spinner("Saving…"):
        r = save_profile(user_id, {
            "native_language": native_lang,
            "danish_level": danish_level,
            "goal": goal,
            "challenges": challenges,
        })
    if isinstance(r, BridgeError):
        st.error(BRIDGE_UNREACHABLE_MSG)
    else:
        st.success("Goals updated.")

st.divider()

# ---------------------------------------------------------------------------
# Integrations
# ---------------------------------------------------------------------------
st.subheader("Integrations")

google_status = get_google_status()
cal_connected = not isinstance(google_status, BridgeError) and google_status.get("data", {}).get("calendar")
gmail_connected = not isinstance(google_status, BridgeError) and google_status.get("data", {}).get("gmail")

col1, col2 = st.columns(2)
with col1:
    st.write("**Google Calendar**")
    if cal_connected:
        st.success("Connected")
    else:
        st.caption("Not connected")
        if st.button("Connect Calendar"):
            url_result = get_google_auth_url()
            if isinstance(url_result, BridgeError):
                st.error(url_result.message)
            else:
                st.link_button("Open Google consent screen", url_result["data"]["url"])

with col2:
    st.write("**Gmail**")
    if gmail_connected:
        st.success("Connected")
    else:
        st.caption("Not connected")
        if st.button("Connect Gmail"):
            url_result = get_google_auth_url()
            if isinstance(url_result, BridgeError):
                st.error(url_result.message)
            else:
                st.link_button("Open Google consent screen", url_result["data"]["url"])

st.divider()

# ---------------------------------------------------------------------------
# WhatsApp
# ---------------------------------------------------------------------------
st.subheader("WhatsApp")
st.write(f"Linked number: **{st.session_state.get('whatsapp_number', '—')}**")
if st.button("Re-link WhatsApp number"):
    with st.spinner("Triggering re-link…"):
        r = relink_whatsapp(user_id)
    if isinstance(r, BridgeError):
        st.error(r.message)
    else:
        st.info("Check your WhatsApp — a new QR flow has been triggered on the VPS.")

st.divider()

# ---------------------------------------------------------------------------
# Danger zone
# ---------------------------------------------------------------------------
st.subheader("⚠️ Danger zone")
st.caption("This permanently erases all your tutor memory.")
confirm = st.text_input("Type RESET to confirm", key="danger_confirm")
if st.button("Reset all memory", type="secondary"):
    if confirm == "RESET":
        with st.spinner("Resetting…"):
            r = update_raw_memory(user_id, {
                "profile.md": "",
                "lesson_plan.md": "",
                "lesson_history.md": "",
            })
        if isinstance(r, BridgeError):
            st.error(r.message)
        else:
            st.success("Memory cleared. Your tutor starts fresh on the next message.")
    else:
        st.error("Type RESET to confirm.")
