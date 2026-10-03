"""Local unlimited TTS service built on Piper (ONNX, runs fully offline)."""

import io
import wave
from pathlib import Path
from threading import Lock

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from piper import PiperVoice, SynthesisConfig
from pydantic import BaseModel, Field

VOICE_DIR = Path(__file__).parent / "voices"

VOICES = {
    "hi": "hi_IN-rohan-medium",
    "hi-f": "hi_IN-priyamvada-medium",
    "mr": "mr_IN-google-medium",
    "te": "te_IN-maya-medium",
    "te-m": "te_IN-venkatesh-medium",
    "bn": "bn_BD-google-medium",
    "ml": "ml_IN-arjun-medium",
    "ur": "ur_PK-fasih-medium",
    "en": "en_US-lessac-medium",
}

LANGUAGES = {
    "hi": "Hindi",
    "hi-f": "Hindi (female)",
    "mr": "Marathi",
    "te": "Telugu",
    "te-m": "Telugu (male)",
    "bn": "Bengali",
    "ml": "Malayalam",
    "ur": "Urdu",
    "en": "English",
}

app = FastAPI(title="Indic.ai TTS", version="1.0.0")

_loaded: dict[str, PiperVoice] = {}
_load_lock = Lock()


def get_voice(name: str) -> PiperVoice:
    if name not in VOICES:
        raise HTTPException(400, f"Unknown voice '{name}'. Available: {sorted(VOICES)}")
    if name not in _loaded:
        with _load_lock:
            if name not in _loaded:
                stem = VOICES[name]
                _loaded[name] = PiperVoice.load(
                    VOICE_DIR / f"{stem}.onnx",
                    config_path=VOICE_DIR / f"{stem}.onnx.json",
                )
    return _loaded[name]


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to speak")
    voice: str = Field("hi", description="Voice name: hi or en")
    speed: float = Field(1.0, ge=0.5, le=2.0, description="Speed multiplier (>1 faster)")


@app.get("/")
def root():
    return {
        "service": "Indic.ai TTS",
        "engine": "piper (local, unlimited, offline)",
        "voices": sorted(VOICES),
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "ok", "loaded": sorted(_loaded)}


@app.get("/voices")
def voices():
    return {
        "voices": [
            {"name": n, "language": LANGUAGES.get(n, "?"), "model": m} for n, m in VOICES.items()
        ]
    }


@app.post("/tts")
def tts(req: TTSRequest):
    voice = get_voice(req.voice)
    syn_config = SynthesisConfig(length_scale=1.0 / req.speed)

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav_file:
        voice.synthesize_wav(req.text, wav_file, syn_config=syn_config)

    audio = buf.getvalue()
    if not audio:
        raise HTTPException(
            422, "No audio produced. Send UTF-8 encoded text (set Content-Type charset=utf-8)."
        )

    return Response(
        content=audio,
        media_type="audio/wav",
        headers={"Content-Disposition": "attachment; filename=speech.wav"},
    )
