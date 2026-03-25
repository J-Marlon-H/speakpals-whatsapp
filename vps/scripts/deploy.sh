#!/bin/bash
# SpeakPals Tutor — VPS deploy script
# Run once on a fresh Droplet after OpenClaw is installed.
# Usage: bash deploy.sh
set -e

echo "=== SpeakPals Tutor — VPS Deploy ==="

# ---------------------------------------------------------------------------
# System dependencies
# ---------------------------------------------------------------------------
apt update && apt upgrade -y
apt install -y ffmpeg python3-pip python3-venv
# nodejs is already installed via nodesource (npm is bundled with it)

# ---------------------------------------------------------------------------
# ClawHub skill: gog (Google Calendar + Gmail)
# ---------------------------------------------------------------------------
clawhub install gog

# ---------------------------------------------------------------------------
# Memory directory
# ---------------------------------------------------------------------------
mkdir -p /home/openclaw/memory
chmod 700 /home/openclaw/memory

mkdir -p /home/openclaw/config
chmod 700 /home/openclaw/config

# ---------------------------------------------------------------------------
# SQLite vocab DB (shared across users — per-user rows use user_id column)
# ---------------------------------------------------------------------------
python3 - <<'PYEOF'
import sqlite3, os
db_path = "/home/openclaw/memory/vocab.db"
conn = sqlite3.connect(db_path)
conn.execute("""
CREATE TABLE IF NOT EXISTS vocab (
    id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL,
    danish TEXT NOT NULL,
    translation TEXT NOT NULL,
    last_seen DATE,
    next_review DATE,
    interval_days INTEGER DEFAULT 1,
    ease_factor REAL DEFAULT 2.5,
    times_correct INTEGER DEFAULT 0,
    times_wrong INTEGER DEFAULT 0,
    mastered BOOLEAN DEFAULT 0
)
""")
conn.commit()
conn.close()
print("SQLite vocab DB ready at", db_path)
PYEOF

# ---------------------------------------------------------------------------
# FastAPI bridge
# ---------------------------------------------------------------------------
mkdir -p /home/openclaw/bridge
cp -r /root/speakpals-whatsapp/vps/bridge/* /home/openclaw/bridge/

cd /home/openclaw/bridge
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn python-dotenv websockets httpx google-auth-oauthlib

# ---------------------------------------------------------------------------
# OpenClaw skills
# ---------------------------------------------------------------------------
mkdir -p ~/.openclaw/skills
cp -r /root/speakpals-whatsapp/vps/skills/* ~/.openclaw/skills/

# ---------------------------------------------------------------------------
# OpenClaw config
# ---------------------------------------------------------------------------
mkdir -p ~/.openclaw
cp /root/speakpals-whatsapp/vps/config/openclaw.yaml ~/.openclaw/config.yaml
echo "Remember to set your WhatsApp number in ~/.openclaw/config.yaml (allowFrom)"

# ---------------------------------------------------------------------------
# Systemd service for FastAPI bridge
# ---------------------------------------------------------------------------
cat > /etc/systemd/system/speakpals-bridge.service << 'EOF'
[Unit]
Description=SpeakPals FastAPI Bridge
After=network.target

[Service]
User=root
WorkingDirectory=/home/openclaw/bridge
EnvironmentFile=/home/openclaw/.env
ExecStart=/home/openclaw/bridge/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable speakpals-bridge
systemctl start speakpals-bridge

echo ""
echo "=== Deploy complete ==="
echo ""
echo "Next steps (in order):"
echo "  1. Edit ~/.openclaw/config.yaml — set your WhatsApp number in allowFrom"
echo "  2. Run: openclaw channels login --channel whatsapp  (scan QR from phone)"
echo "  3. Upload google_credentials.json: scp from your laptop"
echo "  4. Run: node /root/speakpals-whatsapp/vps/scripts/gog_auth.js  (Google OAuth)"
echo "  5. Open Streamlit app and register your WhatsApp number"
echo ""
echo "Check bridge logs: journalctl -u speakpals-bridge -f"
echo "Check OpenClaw logs: journalctl -u openclaw -f"
