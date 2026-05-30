# KittenTTS Local Provider

OpenAI-compatible TTS server using [KittenTTS](https://github.com/KittenML/KittenTTS) models.

## Features

- 🚀 **Lightweight** — Models from 15M to 80M parameters
- 🔊 **8 voices** — Bella, Jasper, Luna, Bruno, Rosie, Hugo, Kiki, Leo
- 📡 **OpenAI-compatible API** — Drop-in replacement for OpenAI TTS
- 🐳 **Docker Ready** — One command to deploy

## Quick Start

```bash
# Clone and configure
cp .env.example .env
# Edit .env to choose model size and voice

# Start
docker compose up -d

# Test
curl -X POST http://localhost:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"input": "Hello, world!", "voice": "Jasper"}' \
  --output test.mp3
```

## API Endpoints

### `POST /v1/audio/speech`

OpenAI-compatible TTS endpoint.

**Request:**
```json
{
  "model": "kitten-tts",
  "input": "Hello, world!",
  "voice": "Jasper",
  "speed": 1.0
}
```

**Response:** Audio file (MP3)

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
| `KITTEN_MODEL_SIZE` | nano | Model: nano, nano-int8, micro, mini |
| `SAMPLE_RATE` | 24000 | Audio sample rate |
| `DEFAULT_VOICE` | Jasper | Default voice |
| `CORS_ORIGINS` | * | CORS origins |

## Voice Mapping

KittenTTS voices mapped to OpenAI-style names for compatibility:

| OpenAI Voice | KittenTTS Voice |
|--------------|-----------------|
| alloy | Jasper |
| echo | Hugo |
| fable | Leo |
| onyx | Bruno |
| nova | Luna |
| shimmer | Bella |
| asteroid | Kiki |
| sage | Rosie |

## Models

| Model | Params | Size | Speed | Quality |
|-------|--------|------|-------|---------|
| nano | 15M | ~25MB | Fastest | Good |
| nano-int8 | 15M | ~25MB | Fast | Good |
| micro | 40M | ~41MB | Medium | Better |
| mini | 80M | ~80MB | Slower | Best |

## Using with Hermes

In your Hermes config, add the openai provider pointing to this server:

```yaml
tts:
  provider: openai
  openai:
    model: kitten-tts
    voice: Jasper
    base_url: http://YOUR_PC_IP:8000/v1
```

## License

[WTFPL](LICENSE) — Do What The F*ck You Want To Public License
