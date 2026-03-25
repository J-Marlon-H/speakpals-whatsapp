"""
SpeakPals FastAPI bridge.
Thin REST layer between Streamlit Cloud and the OpenClaw agent on the VPS.
"""
import logging
import os

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

load_dotenv("/home/openclaw/.env")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="SpeakPals Bridge", version="1.0.0")
security = HTTPBearer()


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> None:
    """Reject requests that don't carry the shared BRIDGE_API_KEY."""
    expected = os.environ.get("BRIDGE_API_KEY", "")
    if not expected or credentials.credentials != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


# Register route modules (all routes require verify_token via the router dependency)
from routes import users, memory, schedule, trigger, integrations  # noqa: E402

app.include_router(users.router, prefix="/users", dependencies=[Depends(verify_token)])
app.include_router(memory.router, prefix="/memory", dependencies=[Depends(verify_token)])
app.include_router(schedule.router, prefix="/users", dependencies=[Depends(verify_token)])
app.include_router(trigger.router, prefix="/lessons", dependencies=[Depends(verify_token)])
app.include_router(integrations.router, prefix="/integrations", dependencies=[Depends(verify_token)])


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
