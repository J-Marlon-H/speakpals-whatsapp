"""
Secret/config loader.
Reads from Streamlit secrets in production, falls back to keys.env for local dev.
"""
import os
from dotenv import load_dotenv

_env_loaded = False


def get_secret(key: str) -> str:
    """Return a secret value by key name.

    Tries st.secrets first (Streamlit Cloud), then keys.env (local dev).
    Raises KeyError if the key is not found in either.
    """
    try:
        import streamlit as st
        # st.secrets supports flat keys and nested [section] keys
        if key in st.secrets:
            return st.secrets[key]
        # Also search nested sections
        for section in st.secrets:
            if hasattr(st.secrets[section], "__getitem__"):
                try:
                    return st.secrets[section][key]
                except (KeyError, TypeError):
                    pass
    except Exception:
        pass

    # Fall back to environment / keys.env
    global _env_loaded
    if not _env_loaded:
        load_dotenv("keys.env")
        _env_loaded = True

    value = os.environ.get(key)
    if value is None:
        raise KeyError(
            f"Secret '{key}' not found in st.secrets or keys.env. "
            "Add it to keys.env for local dev or Streamlit Cloud secrets for production."
        )
    return value
