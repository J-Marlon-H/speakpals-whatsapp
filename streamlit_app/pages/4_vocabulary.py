"""Vocabulary tracker with SRS status and filters."""
import streamlit as st
import pandas as pd

from utils.bridge_client import BridgeError, get_vocab, update_vocab_word
from utils.constants import APP_ICON, BRIDGE_UNREACHABLE_MSG

st.set_page_config(page_title="Vocabulary – SpeakPals", page_icon=APP_ICON)

if not st.session_state.get("user_id"):
    st.warning("Please complete onboarding first.")
    st.stop()

user_id = st.session_state.user_id

st.title("📖 Vocabulary")

with st.spinner("Loading vocabulary…"):
    result = get_vocab(user_id)

if isinstance(result, BridgeError):
    st.error(BRIDGE_UNREACHABLE_MSG)
    st.caption(result.message)
    st.stop()

words = result.get("data", {}).get("words", [])

if not words:
    st.info("No vocabulary tracked yet. Your tutor will add words as you learn them.")
    st.stop()

df = pd.DataFrame(words)

# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------
filter_col1, filter_col2 = st.columns(2)
with filter_col1:
    filter_mode = st.radio(
        "Show",
        ["All", "Due today", "Struggling (3+ errors)", "Recently added"],
        horizontal=True,
    )
with filter_col2:
    search = st.text_input("Search", placeholder="Filter by Danish or translation…")

if filter_mode == "Due today":
    today = pd.Timestamp.today().normalize()
    df = df[pd.to_datetime(df["next_review"]) <= today]
elif filter_mode == "Struggling (3+ errors)":
    df = df[df["times_wrong"] >= 3]
elif filter_mode == "Recently added":
    df = df.sort_values("last_seen", ascending=False).head(20)

if search:
    mask = (
        df["danish"].str.contains(search, case=False, na=False) |
        df["translation"].str.contains(search, case=False, na=False)
    )
    df = df[mask]

# ---------------------------------------------------------------------------
# Table
# ---------------------------------------------------------------------------
display_cols = ["danish", "translation", "last_seen", "next_review", "times_correct", "times_wrong"]
available_cols = [c for c in display_cols if c in df.columns]
st.dataframe(df[available_cols], use_container_width=True, hide_index=True)

st.caption(f"{len(df)} word(s) shown")

# ---------------------------------------------------------------------------
# Mark as mastered
# ---------------------------------------------------------------------------
st.divider()
st.subheader("Mark a word as mastered")

word_options = df["danish"].tolist() if not df.empty else []
if word_options:
    selected = st.selectbox("Choose a word", word_options)
    if st.button("✅ Mark as mastered"):
        word_id = int(df[df["danish"] == selected].iloc[0]["id"])
        with st.spinner("Updating…"):
            r = update_vocab_word(user_id, word_id, {"mastered": True})
        if isinstance(r, BridgeError):
            st.error(r.message)
        else:
            st.success(f"'{selected}' marked as mastered.")
            st.rerun()
