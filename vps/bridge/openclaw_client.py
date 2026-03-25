"""
WebSocket client for the OpenClaw Gateway.
Sends plain-text commands to the agent and returns its response.
"""
import asyncio
import logging
import os

import websockets

logger = logging.getLogger(__name__)

GATEWAY_URL = os.environ.get("OPENCLAW_GATEWAY_URL", "ws://127.0.0.1:18789")
GATEWAY_TOKEN = os.environ.get("OPENCLAW_GATEWAY_TOKEN", "")  # HUMAN DEPENDENCY: set after wizard


async def _send(command: str) -> str:
    """Open a WebSocket connection, send a command, and return the response."""
    async with websockets.connect(
        GATEWAY_URL,
        additional_headers={"Authorization": f"Bearer {GATEWAY_TOKEN}"},
    ) as ws:
        await ws.send(command)
        response = await ws.recv()
        logger.info("OpenClaw response received (%d chars)", len(response))
        return response


def run_command(command: str) -> str:
    """Synchronous wrapper around _send — safe to call from FastAPI route handlers."""
    return asyncio.run(_send(command))
