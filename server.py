"""
Silero TTS Local Provider
OpenAI-compatible TTS server using Silero models via torch.hub
"""

import os
import io
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

# Config from env
PORT = int(os.getenv("PORT", "8000"))
HOST = os.getenv("HOST", "0.0.0.0")
SAMPLE_RATE = int(os.getenv("SAMPLE_RATE", "24000"))
DEFAULT_VOICE = os.getenv("DEFAULT_VOICE", "aidar")
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "ru")
MODEL_VERSION = os.getenv("MODEL_VERSION", "v5_5_ru")

# Map OpenAI-style voices to Silero speakers
VOICE_MAP = {
    "alloy": "aidar",
    "echo": "baya",
    "fable": "kseniya",
    "onyx": "kseniya_v2",
    "nova": "eugene",
    "shimmer": "aidar",
    "asteroid": "aidar",
    "sage": "aidar",
    # Native Silero voices
    "aidar": "aidar",
    "baya": "baya",
    "kseniya": "kseniya",
    "kseniya_v2": "kseniya_v2",
    "eugene": "eugene",
}

# Valid Russian voices for v5_ru models
VALID_VOICES = ["aidar", "baya", "kseniya", "kseniya_v2", "eugene"]

# Load model via torch.hub with trust_repo=True
logger.info(f"Loading Silero model: {MODEL_VERSION}, speaker: {DEFAULT_VOICE}")
device = torch.device("cpu")

# Silero models repo - trust_repo=True allows download without prompt
model, example_text = torch.hub.load(
    repo_or_dir="snakers4/silero-models",
    model="silero_tts",
    language=DEFAULT_LANGUAGE,
    speaker=DEFAULT_VOICE,
    trust_repo=True,
)
model.to(device)
logger.info(f"Model loaded. Example text: {example_text}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Silero TTS server started on {HOST}:{PORT}")
    logger.info(f"Model: {MODEL_VERSION}, Language: {DEFAULT_LANGUAGE}")
    yield
    logger.info("Silero TTS server stopped")


app = FastAPI(title="Silero TTS Local Provider", lifespan=lifespan)


class SpeechRequest(BaseModel):
    model: str = "silero-tts"
    input: str
    voice: str = DEFAULT_VOICE
    language: Optional[str] = DEFAULT_LANGUAGE
    speed: Optional[float] = 1.0
    response_format: str = "mp3"
    sample_rate: Optional[int] = SAMPLE_RATE
    stream: bool = False


@app.post("/v1/audio/speech")
async def text_to_speech(request: SpeechRequest):
    """OpenAI-compatible /v1/audio/speech endpoint"""
    if not request.input:
        raise HTTPException(status_code=400, detail="input is required")

    # Map voice name
    speaker = VOICE_MAP.get(request.voice.lower(), request.voice)

    # Validate voice
    if speaker not in VALID_VOICES:
        raise HTTPException(
            status_code=400,
            detail=f"Voice '{speaker}' not available. Available: {VALID_VOICES}"
        )

    # Generate audio
    try:
        sr = request.sample_rate or SAMPLE_RATE
        # New Silero API uses 'texts' (list), old uses 'text'
        try:
            audio = model.apply_tts(
                texts=[request.input],
                speaker=speaker,
                sample_rate=sr,
            )[0]
        except TypeError:
            # Fallback to old API
            audio = model.apply_tts(
                text=request.input,
                speaker=speaker,
                sample_rate=sr,
            )
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {e}")

    # Convert numpy array to WAV bytes
    audio_bytes = io.BytesIO()
    audio_int16 = (np.clip(audio, -1, 1) * 32767).astype(np.int16)

    import wave
    with wave.open(audio_bytes, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(audio_int16.tobytes())

    audio_bytes.seek(0)
    return Response(content=audio_bytes.read(), media_type="audio/wav")


@app.get("/v1/models")
async def list_models():
    """List available models"""
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
    """List available voices"""
    return {
        "object": "list",
        "data": [
            {"id": v, "name": v, "language": DEFAULT_LANGUAGE}
            for v in VALID_VOICES
        ]
    }


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "ok", "model": MODEL_VERSION, "language": DEFAULT_LANGUAGE}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
