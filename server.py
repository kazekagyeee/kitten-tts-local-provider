"""
Silero TTS Local Provider
OpenAI-compatible TTS server using Silero models
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

from silero import silero_tts

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
    "onyx": "xenia",
    "nova": "eugene",
    "shimmer": "aidar",
    "asteroid": "aidar",
    "sage": "aidar",
    # Native Silero voices
    "aidar": "aidar",
    "baya": "baya",
    "kseniya": "kseniya",
    "xenia": "xenia",
    "eugene": "eugene",
}

# Load model
logger.info(f"Loading Silero model: {MODEL_VERSION}")
device = torch.device("cpu")
model, example_text = silero_tts(language=DEFAULT_LANGUAGE, speaker=DEFAULT_VOICE)
model.to(device)
logger.info(f"Model loaded. Example: {example_text}")


def get_audio_format(requested_format: str) -> str:
    """Map requested format to actual format"""
    format_map = {
        "mp3": "mp3",
        "wav": "wav",
        "ogg": "ogg",
        "opus": "opus",
    }
    return format_map.get(requested_format.lower(), "mp3")


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

    # Generate audio
    try:
        # Silero expects sample_rate as int
        audio = model.apply_tts(
            text=request.input,
            speaker=speaker,
            sample_rate=request.sample_rate or SAMPLE_RATE,
        )
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {e}")

    # Convert numpy array to bytes
    audio_bytes = io.BytesIO()
    if request.response_format.lower() == "wav":
        import wave
        sample_rate = request.sample_rate or SAMPLE_RATE
        audio_int16 = (np.clip(audio, -1, 1) * 32767).astype(np.int16)
        with wave.open(audio_bytes, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(audio_int16.tobytes())
    else:
        # For mp3/ogg - save as wav first, let the client handle conversion
        import wave
        sample_rate = request.sample_rate or SAMPLE_RATE
        audio_int16 = (np.clip(audio, -1, 1) * 32767).astype(np.int16)
        with wave.open(audio_bytes, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
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
    voices = ["aidar", "baya", "kseniya", "xenia", "eugene"]
    return {
        "object": "list",
        "data": [
            {"id": v, "name": v, "language": DEFAULT_LANGUAGE}
            for v in voices
        ]
    }


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "ok", "model": MODEL_VERSION, "language": DEFAULT_LANGUAGE}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
