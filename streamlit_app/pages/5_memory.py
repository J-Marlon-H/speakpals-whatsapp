"""Raw memory viewer and editor."""
import streamlit as st

from utils.bridge_client import BridgeError, get_raw_memory, update_raw_memory
from utils.constants import APP_ICON, BRIDGE_UNREACHABLE_MSG

st.set_page_config(page_title="Memory – SpeakPals", page_icon=APP_ICON)

if not st.session_state.get("user_id"):
    st.warning("Please complete onboarding first.")
    st.stop()

user_id = st.session_state.user_id

st.title("🧠 Memory")
st.warning(
    "Editing memory directly changes what your tutor knows about you. "
    "Be careful — your tutor reads these files on every message."
)

with st.spinner("Loading memory files…"):
    result = get_raw_memory(user_id)

if isinstance(result, BridgeError):
    st.error(BRIDGE_UNREACHABLE_MSG)
    st.caption(result.message)
    st.stop()

files: dict = result.get("data", {})
SECTION_LABELS = {
    "profile.md": "Student Profile",
    "lesson_plan.md": "Lesson Plan",
    "lesson_history.md": "Lesson History",
}

for filename, label in SECTION_LABELS.items():
    content = files.get(filename, "")
    with st.expander(label, expanded=False):
        if st.toggle(f"Edit {label}", key=f"edit_{filename}"):
            new_content = st.text_area(
                "Content (markdown)",
                value=content,
                height=300,
                key=f"textarea_{filename}",
            )
            if st.button("Save", key=f"save_{filename}"):
                with st.spinner("Saving…"):
                    r = update_raw_memory(user_id, {filename: new_content})
                if isinstance(r, BridgeError):
                    st.error(r.message)
                else:
                    st.success("Saved.")
                    st.rerun()
        else:
            st.code(content, language="markdown")
