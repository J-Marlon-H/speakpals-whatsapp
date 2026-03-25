"""
SpeakPals – entry point.
Sets page config, handles session-state auth, and renders the sidebar nav.
"""
import streamlit as st

from utils.constants import APP_TITLE, APP_ICON

st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="centered",
)

# ---------------------------------------------------------------------------
# Session state defaults
# ---------------------------------------------------------------------------
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "whatsapp_number" not in st.session_state:
    st.session_state.whatsapp_number = None

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title(f"{APP_ICON} {APP_TITLE}")

    if st.session_state.user_id:
        st.caption(f"Linked: {st.session_state.whatsapp_number}")
        st.page_link("pages/2_dashboard.py", label="Dashboard", icon="🏠")
        st.page_link("pages/3_lesson_plan.py", label="Lesson Plan", icon="📅")
        st.page_link("pages/4_vocabulary.py", label="Vocabulary", icon="📖")
        st.page_link("pages/5_memory.py", label="Memory", icon="🧠")
        st.page_link("pages/6_settings.py", label="Settings", icon="⚙️")
        st.divider()
        if st.button("Log out"):
            st.session_state.user_id = None
            st.session_state.whatsapp_number = None
            st.rerun()
    else:
        st.page_link("pages/1_onboarding.py", label="Get started", icon="👋")

# ---------------------------------------------------------------------------
# Home / redirect
# ---------------------------------------------------------------------------
if not st.session_state.user_id:
    st.title(f"{APP_ICON} Welcome to SpeakPals")
    st.write(
        "Your personal Danish tutor lives in WhatsApp. "
        "Use the control panel here to set your goals, schedule, and track progress."
    )
    st.page_link("pages/1_onboarding.py", label="→ Set up your account", icon="👋")
else:
    st.switch_page("pages/2_dashboard.py")
