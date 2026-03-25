"""Google OAuth routes."""
import json
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

# HUMAN DEPENDENCY: google-auth-oauthlib must be installed and
# google_credentials.json uploaded to the VPS (see HUMAN_SETUP_INSTRUCTIONS Part 1.3)
try:
    from google_auth_oauthlib.flow import Flow
    _GOOGLE_AVAILABLE = True
except ImportError:
    _GOOGLE_AVAILABLE = False

router = APIRouter()

CREDENTIALS_PATH = Path(os.environ.get("GOOGLE_CREDENTIALS_PATH", "/home/openclaw/config/google_credentials.json"))
TOKEN_PATH = Path(os.environ.get("GOOGLE_TOKEN_PATH", "/home/openclaw/config/google_token.json"))
REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:8000/integrations/google/callback")

SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/gmail.readonly",
]


def _get_flow() -> "Flow":
    if not _GOOGLE_AVAILABLE:
        raise HTTPException(status_code=501, detail="google-auth-oauthlib not installed")
    if not CREDENTIALS_PATH.exists():
        raise HTTPException(
            status_code=503,
            detail="google_credentials.json not found on VPS. See HUMAN_SETUP_INSTRUCTIONS Part 1.3.",
        )
    return Flow.from_client_secrets_file(str(CREDENTIALS_PATH), scopes=SCOPES, redirect_uri=REDIRECT_URI)


@router.get("/google/auth-url")
def get_auth_url() -> dict:
    """Return the Google OAuth consent screen URL."""
    flow = _get_flow()
    auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline")
    return {"status": "ok", "data": {"url": auth_url}}


@router.get("/google/callback")
def oauth_callback(request: Request) -> dict:
    """Handle the OAuth redirect and save the token to disk."""
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Missing code parameter")

    flow = _get_flow()
    flow.fetch_token(code=code)
    token_data = {
        "token": flow.credentials.token,
        "refresh_token": flow.credentials.refresh_token,
        "token_uri": flow.credentials.token_uri,
        "client_id": flow.credentials.client_id,
        "client_secret": flow.credentials.client_secret,
        "scopes": list(flow.credentials.scopes or []),
    }
    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_PATH.write_text(json.dumps(token_data, indent=2))
    return {"status": "ok", "data": {"message": "Google account connected."}}


@router.get("/google/status")
def get_status() -> dict:
    """Return whether Google Calendar and Gmail are connected."""
    if not TOKEN_PATH.exists():
        return {"status": "ok", "data": {"calendar": False, "gmail": False}}

    token_data = json.loads(TOKEN_PATH.read_text())
    scopes = token_data.get("scopes", [])
    return {
        "status": "ok",
        "data": {
            "calendar": "https://www.googleapis.com/auth/calendar" in scopes,
            "gmail": "https://www.googleapis.com/auth/gmail.readonly" in scopes,
        },
    }
