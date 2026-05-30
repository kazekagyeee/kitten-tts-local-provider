# Silero TTS Local Provider

OpenAI-compatible TTS server using [Silero](https://github.com/snakers4/silero-models) models.

## Features

- 🗣️ **Russian language** — Native Russian TTS with auto-stress and homograph support
- 🎭 **5 voices** — aidar, baya, kseniya, xenia, eugene
- 📡 **OpenAI-compatible API** — Drop-in replacement for OpenAI TTS
- 🐳 **Docker Ready** — One command to deploy
- 🔥 **Fast on CPU** — Optimized for real-time inference

## Quick Start

```bash
# Clone and configure
git clone git@github.com:kazekagyeee/silero-tts-local-provider.git
cd silero-tts-local-provider
cp .env.example .env
# Edit .env to choose voice

# Start
docker compose up -d

# Test
curl -X POST http://localhost:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"input": "Привет, мир!", "voice": "aidar"}' \
  --output test.wav
```

## API Endpoints

### `POST /v1/audio/speech`

OpenAI-compatible TTS endpoint.

**Request:**
```json
{
  "model": "silero-tts",
  "input": "Привет, мир!",
  "voice": "aidar",
  "language": "ru",
  "speed": 1.0,
  "sample_rate": 24000
}
```

**Response:** Audio file (WAV/MP3)

### `GET /v1/voices`

List available voices.

### `GET /v1/models`

List available models.

### `GET /health`

Health check endpoint.

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 8000 | Server port |
| `HOST` | 0.0.0.0 | Server host |
| `SAMPLE_RATE` | 24000 | Audio sample rate (8000, 24000, 48000) |
| `DEFAULT_VOICE` | aidar | Default voice |
| `DEFAULT_LANGUAGE` | ru | Language code |
| `MODEL_VERSION` | v5_5_ru | Model version |

## Voices

| Voice | Gender | Description |
|-------|--------|-------------|
| aidar | Male | Deep, authoritative |
| baya | Female | Warm, friendly |
| kseniya | Female | Clear, professional |
| xenia | Female | Soft, calm |
| eugene | Male | Standard, neutral |

## Model Versions

| Version | Quality | Auto-stress | Homographs | Questions |
|---------|---------|-------------|------------|-----------|
| v5_5_ru | Best | ✅ | ✅ | ✅ |
| v5_4_ru | Good | ✅ | ✅ | ✅ |
| v5_3_ru | Standard | ✅ | ✅ | ❌ |
| v5_2_ru | Standard | ✅ | ✅ | ❌ |
| v5_ru | Standard | ✅ | ✅ | ❌ |

## Using with Hermes

In your Hermes config, add the openai provider pointing to this server:

```yaml
tts:
  provider: openai
  openai:
    model: silero-tts
    voice: aidar
    base_url: http://YOUR_PC_IP:8000/v1
```

## License

[WTFPL](LICENSE) — Do What The F*ck You Want To Public License
