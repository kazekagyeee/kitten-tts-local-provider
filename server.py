"""
Silero TTS Local Provider
OpenAI-compatible TTS server using Silero v5 models via torch.hub

Model: v5_5_ru (multi-speaker: aidar, baya, kseniya, xenia, eugene)
Inference: model.save_wav(text=..., speaker=..., sample_rate=...)
"""

import os
import logging
from contextlib import asynccontextmanager
from typing import Optional

import torch
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Config from env ──────────────────────────────────────────────────────────
PORT = int(os.getenv("PORT", "8000"))
HOST = os.getenv("HOST", "0.0.0.0")
SAMPLE_RATE = int(os.getenv("SAMPLE_RATE", "24000"))
DEFAULT_VOICE = os.getenv("DEFAULT_VOICE", "aidar")
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "ru")
MODEL_VERSION = os.getenv("MODEL_VERSION", "v5_5_ru")
PREFERRED_GENDER = os.getenv("PREFERRED_GENDER", "").strip().lower()  # "", "male", "female"

# ── Voice registry with gender ────────────────────────────────────────────────
# v5_5_ru speakers: aidar, baya, kseniya, xenia, eugene
VOICES = {
    "aidar":   {"gender": "male",   "description": "Мужской, глубокий"},
    "baya":    {"gender": "female", "description": "Женский, тёплый"},
    "kseniya": {"gender": "female", "description": "Женский, чёткий"},
    "xenia":   {"gender": "female", "description": "Женский, мягкий"},
    "eugene":  {"gender": "male",   "description": "Мужской, стандартный"},
}

# OpenAI voice name mapping
VOICE_MAP = {
    "alloy": "aidar", "echo": "baya", "fable": "kseniya",
    "onyx": "eugene", "nova": "eugene", "shimmer": "baya",
    "asteroid": "aidar", "sage": "aidar",
}

def get_valid_voices(gender: str = "") -> list[str]:
    """Return voices filtered by gender. gender='', 'male', or 'female'."""
    if gender not in ("male", "female"):
        return list(VOICES.keys())
    return [v for v, info in VOICES.items() if info["gender"] == gender]

VALID_VOICES = get_valid_voices(PREFERRED_GENDER)
logger.info(f"Voices (gender={PREFERRED_GENDER or 'all'}): {VALID_VOICES}")

# ── Load model ────────────────────────────────────────────────────────────────
# v5_5_ru loads without speaker baked in — speaker is passed at inference
logger.info(f"Loading Silero: {MODEL_VERSION}")
device = torch.device("cpu")

model, example_text = torch.hub.load(
    repo_or_dir="snakers4/silero-models",
    model="silero_tts",
    language=DEFAULT_LANGUAGE,
    speaker=MODEL_VERSION,
    trust_repo=True,
)
model.to(device)
logger.info(f"Model loaded. Example: {example_text}")

# Verify save_wav exists (v5 uses save_wav, not apply_tts)
assert hasattr(model, 'save_wav'), "v5 model must have save_wav method"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Silero TTS on {HOST}:{PORT} | model={MODEL_VERSION} | gender={PREFERRED_GENDER or 'all'}")
    yield
    logger.info("Server stopped")


app = FastAPI(title="Silero TTS Local Provider", lifespan=lifespan)


class SpeechRequest(BaseModel):
    model: str = "silero-tts"
    input: str
    voice: str = DEFAULT_VOICE
    language: Optional[str] = DEFAULT_LANGUAGE
    speed: Optional[float] = 1.0
    response_format: str = "mp3"
    sample_rate: Optional[int] = SAMPLE_RATE


@app.post("/v1/audio/speech")
async def text_to_speech(request: SpeechRequest):
    """OpenAI-compatible /v1/audio/speech"""
    if not request.input:
        raise HTTPException(400, "input is required")

    # Resolve voice
    voice = VOICE_MAP.get(request.voice.lower(), request.voice)
    if voice not in VOICES:
        raise HTTPException(400, f"Unknown voice '{voice}'. Available: {list(VOICES.keys())}")
    if voice not in VALID_VOICES:
        raise HTTPException(400, f"Voice '{voice}' blocked by gender filter ({PREFERRED_GENDER}). Available: {VALID_VOICES}")

    # Generate
    try:
        sr = request.sample_rate or SAMPLE_RATE
        audio_path = model.save_wav(
            text=request.input,
            speaker=voice,
            sample_rate=sr,
        )
        with open(audio_path, 'rb') as f:
            audio_bytes = f.read()
        os.remove(audio_path)
    except Exception as e:
        logger.error(f"TTS failed: {e}")
        raise HTTPException(500, f"TTS generation failed: {e}")

    return Response(content=audio_bytes, media_type="audio/wav")


@app.get("/v1/models")
async def list_models():
    return {
        "object": "list",
        "data": [{
            "id": f"silero-tts-{MODEL_VERSION}",
            "object": "model",
            "created": 1700000000,
            "owned_by": "silero",
        }]
    }


@app.get("/v1/voices")
async def list_voices():
    return {
        "object": "list",
        "data": [
            {"id": v, "name": VOICES[v]["description"], "language": DEFAULT_LANGUAGE, "gender": VOICES[v]["gender"]}
            for v in VALID_VOICES
        ]
    }


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "model": MODEL_VERSION,
        "gender_filter": PREFERRED_GENDER or "all",
        "voices": VALID_VOICES,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)