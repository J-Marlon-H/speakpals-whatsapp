---
name: speakpals-voice-handler
description: Handle incoming WhatsApp voice messages. Use when a student sends an audio message — transcribe it with ElevenLabs Scribe, then pass the transcript to the language-tutor skill. Also use when generating a TTS voice reply.
---

# SpeakPals Voice Handler

## Trigger
- Incoming WhatsApp message contains an audio attachment (.ogg / Opus)
- The language-tutor skill asks for a voice reply

## On incoming voice message
1. Download the .ogg attachment to /tmp
2. Call `voice.transcribe_whatsapp_audio(ogg_path)` to get the transcript
3. Pass the transcript text to the **speakpals-language-tutor** skill as if the student typed it
4. Optionally send a TTS voice reply using `voice.text_to_speech(text)` — only do this if the student previously asked for voice feedback, or if the tutor's response is short enough (< 200 chars)

## On TTS reply request
1. Call `voice.text_to_speech(text)` — returns raw MP3 bytes
2. Send the MP3 as a WhatsApp voice message attachment

## Notes
- ffmpeg must be installed on the Droplet (`apt install ffmpeg -y` — handled by deploy.sh)
- ElevenLabs Scribe supports Danish natively
- Voice ID `ygiXC2Oa1BiHksD3WkJZ` is the Mathias Danish voice — do not change it
