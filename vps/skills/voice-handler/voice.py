"""
Voice handler skill.
Transcribes incoming WhatsApp audio (.ogg) using ElevenLabs Scribe STT,
and generates Danish TTS responses using ElevenLabs Mathias voice.
"""
import logging
import os
import subprocess
import tempfile

import httpx

logger = logging.getLogger(__name__)

ELEVENLABS_API_KEY = os.environ["ELEVENLABS_API_KEY"]
ELEVENLABS_VOICE_ID = "ygiXC2Oa1BiHksD3WkJZ"   # Mathias (Danish)
ELEVENLABS_MODEL = "eleven_multilingual_v2"


def transcribe_whatsapp_audio(ogg_path: str) -> str:
    """Convert WhatsApp .ogg (Opus) to .mp3 and transcribe with ElevenLabs Scribe.

    Args:
        ogg_path: Absolute path to the downloaded .ogg file.

    Returns:
        Transcribed text string.

    Raises:
        subprocess.CalledProcessError: If ffmpeg conversion fails.
        httpx.HTTPStatusError: If ElevenLabs returns an error.
    """
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        mp3_path = tmp.name

    try:
        subprocess.run(
            ["ffmpeg", "-i", ogg_path, "-codec:a", "libmp3lame", "-q:a", "2", mp3_path],
            check=True,
            capture_output=True,
        )
        logger.info("Converted %s -> %s", ogg_path, mp3_path)

        with open(mp3_path, "rb") as f:
            audio_data = f.read()

        response = httpx.post(
            "https://api.elevenlabs.io/v1/speech-to-text",
            headers={"xi-api-key": ELEVENLABS_API_KEY},
            files={"file": ("audio.mp3", audio_data, "audio/mpeg")},
            data={"model_id": "scribe_v1"},
            timeout=30,
        )
        response.raise_for_status()
        transcript = response.json()["text"]
        logger.info("Transcription complete (%d chars)", len(transcript))
        return transcript

    finally:
        try:
            os.unlink(mp3_path)
        except OSError:
            pass


def text_to_speech(text: str) -> bytes:
    """Generate Danish TTS audio using ElevenLabs Mathias voice.

    Args:
        text: The Danish text to synthesise.

    Returns:
        Raw MP3 bytes ready to send as a WhatsApp voice message.

    Raises:
        httpx.HTTPStatusError: If ElevenLabs returns an error.
    """
    response = httpx.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}",
        headers={"xi-api-key": ELEVENLABS_API_KEY},
        json={
            "text": text,
            "model_id": ELEVENLABS_MODEL,
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
        },
        timeout=30,
    )
    response.raise_for_status()
    logger.info("TTS generated (%d bytes)", len(response.content))
    return response.content
