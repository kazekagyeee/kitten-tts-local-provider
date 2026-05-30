"""
KittenTTS Local Provider
OpenAI-compatible TTS server using KittenTTS models
"""

import os
import io
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
import soundfile as sf

from kittentts import KittenTTS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Model mapping
MODEL_MAP = {
    "nano": "KittenML/kitten-tts-nano-0.8",
    "nano-int8": "KittenML/kitten-tts-nano-0.8-int8",
    "micro": "KittenML/kitten-tts-micro-0.8",
    "mini": "KittenML/kitten-tts-mini-0.8",
}

# Voice mapping: OpenAI voice names -> KittenTTS voices
VOICE_MAP = {
    "alloy": "Jasper",
    "echo": "Hugo",
    "fable": "Leo",
    "onyx": "Bruno",
    "nova": "Luna",
    "shimmer": "Bella",
    "asteroid": "Kiki",
    "sage": "Rosie",
}

# Config from env
MODEL_SIZE = os.getenv("KITTEN_MODEL_SIZE", "nano")
PORT = int(os.getenv("PORT", "8000"))
HOST = os.getenv("HOST", "0.0.0.0")
SAMPLE_RATE = int(os.getenv("SAMPLE_RATE", "24000"))
DEFAULT_VOICE = os.getenv("DEFAULT_VOICE", "Jasper")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")

# Load model
model_name = MODEL_MAP.get(MODEL_SIZE, MODEL_MAP["nano"])
logger.info(f"Loading KittenTTS model: {model_name}")
tts = KittenTTS(model_name)
logger.info(f"Model loaded. Available voices: {tts.available_voices}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"KittenTTS server started on {HOST}:{PORT}")
    logger.info(f"Model: {MODEL_SIZE} ({model_name})")
    yield
    logger.info("KittenTTS server stopped")


app = FastAPI(title="KittenTTS Local Provider", lifespan=lifespan)


class SpeechRequest(BaseModel):
    model: str = "kitten-tts"
    input: str
    voice: str = DEFAULT_VOICE
    speed: Optional[float] = 1.0
    response_format: str = "mp3"
    stream: bool = False


@app.post("/v1/audio/speech")
async def text_to_speech(request: SpeechRequest):
    """OpenAI-compatible /v1/audio/speech endpoint"""
    if not request.input:
        raise HTTPException(status_code=400, detail="input is required")

    # Map voice name
    voice = VOICE_MAP.get(request.voice.lower(), request.voice)
    if voice not in tts.available_voices:
        raise HTTPException(
            status_code=400,
            detail=f"Voice '{voice}' not available. Available: {tts.available_voices}"
        )

    # Generate audio
    try:
        audio = tts.generate(request.input, voice=voice, speed=request.speed)
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {e}")

    # Convert to MP3 via WAV in memory
    buf = io.BytesIO()
    sf.write(buf, audio, SAMPLE_RATE, format="WAV")
    buf.seek(0)

    return Response(content=buf.read(), media_type="audio/mpeg")


@app.get("/v1/models")
async def list_models():
    """List available models"""
    return {
        "object": "list",
        "data": [{
            "id": f"kitten-tts-{MODEL_SIZE}",
            "object": "model",
            "created": 1700000000,
            "owned_by": "kittenml",
        }]
    }


@app.get("/v1/voices")
async def list_voices():
    """List available voices"""
    return {
        "object": "list",
        "data": [
            {"id": v.lower(), "name": v, "model": MODEL_SIZE}
            for v in tts.available_voices
        ]
    }


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "ok", "model": MODEL_SIZE}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
