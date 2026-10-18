"""Optional voice features.

* Spoken questions: the browser's built-in SpeechSynthesis API, rendered via a tiny HTML component. Nothing is sent
  to a server; if the browser has no speech support the button reports it.
* Voice answers: Streamlit's microphone widget (``st.audio_input``) records audio; Gemini transcribes it ONLY if the
  user clicks "Transcribe" and an API key exists. The transcript is shown for editing and is never auto-submitted.
  If transcription fails or is unavailable, text input is always available.
"""
from __future__ import annotations

import base64
import html
import json
from typing import Optional

from modules.llm_client import GeminiClient, LLMError


def speak_component_html(text: str) -> str:
    payload = json.dumps(text)
    return f"""
<button id="speak" style="padding:6px 12px;border-radius:6px;border:1px solid #9aa4b2;background:#fff;cursor:pointer;font:14px sans-serif">
  🔊 Read question aloud</button>
<span id="msg" style="font:13px sans-serif;color:#555;margin-left:8px"></span>
<script>
const t = {payload};
const b = document.getElementById('speak'), m = document.getElementById('msg');
if (!('speechSynthesis' in window)) {{ b.disabled = true; m.textContent = 'Speech playback is not supported in this browser.'; }}
b.onclick = () => {{ window.speechSynthesis.cancel(); const u = new SpeechSynthesisUtterance(t); u.rate = 0.95; window.speechSynthesis.speak(u); }};
</script>"""


def transcribe_audio(client: GeminiClient, audio_bytes: bytes, mime_type: str = "audio/wav") -> Optional[str]:
    """Return a transcript, or raise LLMError. Never fabricates text."""
    if not audio_bytes:
        return None
    data = base64.b64encode(audio_bytes).decode("ascii")
    text = client.generate("Transcribe this audio verbatim. Return only the transcript, nothing else. "
                           "If there is no intelligible speech, return exactly: [no speech detected]",
                           audio={"mime_type": mime_type, "data": data}, temperature=0.0)
    text = text.strip()
    return None if text == "[no speech detected]" or not text else text
