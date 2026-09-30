#!/usr/bin/env bash
# macOS / Linux: ffmpeg + faster-whisper for the transcribe launcher.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_CMD="$REPO_DIR/.venv/bin/python3"

WITH_DIARIZE=0
if [[ "${1:-}" == "--with-diarize" ]]; then
  WITH_DIARIZE=1
fi

echo "[transcribe] Checking dependencies..."

if command -v ffmpeg >/dev/null 2>&1; then
  echo "  OK  ffmpeg ($(command -v ffmpeg))"
else
  echo "  MISSING  ffmpeg"
  if command -v brew >/dev/null 2>&1; then
    echo "  Installing via Homebrew..."
    brew install ffmpeg
  else
    echo "  Install ffmpeg (e.g. https://ffmpeg.org/download.html) and re-run."
    exit 1
  fi
fi

if [[ ! -x "$PYTHON_CMD" ]]; then
  echo "  Creating Python environment in $REPO_DIR/.venv..."
  python3 -m venv "$REPO_DIR/.venv"
fi

echo "  Installing Python dependencies..."
PIP_ARGS=(install -q -r "$REPO_DIR/requirements.txt")
if [[ "$WITH_DIARIZE" == "1" ]]; then
  PIP_ARGS+=(pyannote.audio)
fi
"$PYTHON_CMD" -m pip "${PIP_ARGS[@]}"

if "$PYTHON_CMD" -c "import faster_whisper" 2>/dev/null; then
  echo "  OK  faster-whisper import"
else
  echo "  FAILED  faster-whisper still not importable"
  exit 1
fi

if [[ "$WITH_DIARIZE" == "1" ]]; then
  if "$PYTHON_CMD" -c "import pyannote.audio" 2>/dev/null; then
    echo "  OK  pyannote.audio import"
  else
    echo "  FAILED  pyannote.audio still not importable"
    exit 1
  fi
else
  echo "  SKIP optional diarization deps. Run: bash deps.sh --with-diarize"
fi

echo ""
echo "Done. Default model is small; set TRANSCRIBE_MODEL=large-v3 for higher quality (larger download)."
echo "For --diarize, set HF_TOKEN after accepting the pyannote model terms on Hugging Face."
