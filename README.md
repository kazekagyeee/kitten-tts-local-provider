# Silero TTS Local Provider

OpenAI-compatible TTS server using [Silero](https://github.com/snakers4/silero-models) models.

## Features

- 🗣️ **Russian language** — Native Russian TTS with auto-stress and homograph support
- 🎭 **5 voices** — aidar, baya, kseniya, xenia, eugene (all always available, no gender filter)
- 📡 **OpenAI-compatible API** — Drop-in replacement for OpenAI TTS
- 🐳 **Docker Ready** — One command to deploy
- 🔥 **Fast on CPU** — Optimized for real-time inference

## Quick Start

```bash
# Clone and configure
git clone git@github.com:kazekagyeee/silero-tts-local-provider.git
cd silero-tts-local-provider
cp .env.example .env
# Edit .env to choose default voice

# Start
docker compose up -d

# Test
curl -X POST http://localhost:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"input": "Привет, мир!", "voice": "kseniya"}' \
  --output test.wav
```

## API Endpoints

### `POST /v1/audio/speech`

OpenAI-compatible TTS endpoint. **You can switch voices on every request** via the `voice` parameter.

**Request:**
```json
{
  "model": "silero-tts",
  "input": "Привет, мир!",
  "voice": "kseniya",
  "language": "ru",
  "speed": 1.0,
  "sample_rate": 24000
}
```

**Response:** Audio file (WAV)

**Voice parameter** accepts:
- Silero voices: `aidar`, `baya`, `kseniya`, `xenia`, `eugene`
- OpenAI aliases: `alloy`→aidar, `echo`/`shimmer`→baya, `fable`→kseniya, `onyx`/`nova`→eugene

**Example — switch voices on the fly:**
```bash
# Female warm
curl -X POST http://localhost:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"input": "Привет, я baya, тёплый женский голос", "voice": "baya"}' \
  --output baya.wav

# Female soft
curl -X POST http://localhost:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"input": "А я xenia, помягче", "voice": "xenia"}' \
  --output xenia.wav

# Male deep
curl -X POST http://localhost:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"input": "А я aidar, мужской глубокий", "voice": "aidar"}' \
  --output aidar.wav
```

### `GET /v1/voices`

List available voices (always all 5, regardless of `PREFERRED_GENDER`).

### `GET /v1/models`

List available model.

### `GET /health`

Health check endpoint. Returns:
```json
{
  "status": "ok",
  "model": "v5_5_ru",
  "gender_filter": "all",
  "voices": ["aidar", "baya", "kseniya", "xenia", "eugene"]
}
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 8000 | Server port (note: docker-compose maps `${PORT}:8000`) |
| `HOST` | 0.0.0.0 | Server host |
| `SAMPLE_RATE` | 24000 | Audio sample rate (8000, 24000, 48000) |
| `DEFAULT_VOICE` | aidar | Default voice if not specified in request |
| `DEFAULT_LANGUAGE` | ru | Language code |
| `MODEL_VERSION` | v5_5_ru | Model version |
| `PREFERRED_GENDER` | (empty) | Logged only, does not block voices |

> ⚠️ **Port mapping gotcha:** `server.py` reads `PORT` from env and binds uvicorn to it. `docker-compose.yml` maps `${PORT}:8000`. If you set `PORT=8888` in `.env`, uvicorn listens on 8888 **inside** the container, but only port 8000 is exposed. **Set `PORT=8000` in `.env`** to match the compose mapping, OR change the compose port to match.

## Voices

All 5 voices are always available, no filtering:

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
    voice: kseniya  # or any of aidar/baya/xenia/eugene
    base_url: http://YOUR_PC_IP:8000/v1
```

To switch voices per-request, set the `voice` parameter in your TTS tool calls (Hermes `text_to_speech` currently uses the default — to switch dynamically, call the Silero endpoint directly via curl).

## License

[WTFPL](LICENSE) — Do What The F*ck You Want To Public License
