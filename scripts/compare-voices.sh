#!/bin/bash
# Compare all Silero TTS voices with the same test phrase
# Usage: ./scripts/compare-voices.sh [silero_url]
# Default URL: http://localhost:8000

set -e

SILERO_URL="${1:-http://localhost:8000}"
TEST_PHRASE="${TEST_PHRASE:-Привет, это голос %VOICE%, проверка связи.}"
OUTPUT_DIR="${OUTPUT_DIR:-/tmp/silero_compare}"
FORMAT="${FORMAT:-ogg}"  # ogg = telegram voice message, wav = lossless

# Voices available in v5_5_ru
VOICES=(aidar baya kseniya xenia eugene)

mkdir -p "$OUTPUT_DIR"
rm -f "$OUTPUT_DIR"/*

echo "🎙️  Silero TTS voice comparison"
echo "    URL: $SILERO_URL"
echo "    Output: $OUTPUT_DIR"
echo "    Format: $FORMAT"
echo "    Phrase: $TEST_PHRASE"
echo ""

for voice in "${VOICES[@]}"; do
    phrase="${TEST_PHRASE//%VOICE%/$voice}"
    output_file="$OUTPUT_DIR/${voice}.${FORMAT}"

    echo -n "  $voice ... "
    http_code=$(curl -s -m 30 -X POST "$SILERO_URL/v1/audio/speech" \
        -H "Content-Type: application/json" \
        -d "{\"input\": \"$phrase\", \"voice\": \"$voice\"}" \
        -o "$output_file" \
        -w "%{http_code}")

    if [ "$http_code" = "200" ] && [ -s "$output_file" ]; then
        size=$(stat -c%s "$output_file" 2>/dev/null || stat -f%z "$output_file")
        echo "✓ HTTP $http_code, ${size} bytes"
    else
        echo "✗ HTTP $http_code, FAILED"
        rm -f "$output_file"
    fi
done

echo ""
echo "📁 Files:"
ls -la "$OUTPUT_DIR"/

# Optional: convert wav → ogg for Telegram voice messages
if [ "$FORMAT" = "ogg" ] && command -v ffmpeg &> /dev/null; then
    echo ""
    echo "🔄 Converting to ogg (Telegram voice format)..."
    for voice in "${VOICES[@]}"; do
        wav="$OUTPUT_DIR/${voice}.wav"
        ogg="$OUTPUT_DIR/${voice}.ogg"
        if [ -f "$wav" ]; then
            ffmpeg -y -i "$wav" -c:a libopus -b:a 32k "$ogg" 2>/dev/null
            rm -f "$wav"
            echo "  ✓ $voice.ogg"
        fi
    done
    echo ""
    echo "🎧 Ready to send. Files in $OUTPUT_DIR"
fi
