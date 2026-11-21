#!/bin/bash
# Runs the existing application locally; no cloud credentials are copied.
set -euo pipefail
cd "$(dirname "$0")"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This launcher is for macOS. On Linux use python -m scripts.run_demo --port 8011."
  exit 1
fi

export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
if ! command -v brew >/dev/null 2>&1; then
  echo "Install Homebrew from https://brew.sh, then run this launcher again."
  exit 1
fi

echo "Preparing local Python, PDF and OCR dependencies with Homebrew..."
brew install python@3.12 pango tesseract
python_bin="$(brew --prefix python@3.12)/bin/python3.12"
brew_lib="$(brew --prefix)/lib"
export DYLD_FALLBACK_LIBRARY_PATH="${brew_lib}${DYLD_FALLBACK_LIBRARY_PATH:+:$DYLD_FALLBACK_LIBRARY_PATH}"
mkdir -p runtime/cache
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-$PWD/runtime/cache}"

if [[ ! -x runtime/macos-venv/bin/python ]]; then
  "$python_bin" -m venv runtime/macos-venv
fi
python_bin="$PWD/runtime/macos-venv/bin/python"
"$python_bin" -m pip install --require-hashes -r requirements.lock
if [[ ! -f runtime/demo-lawyer-password ]]; then
  "$python_bin" -m scripts.seed_demo
fi

local_port="${NYAYSAATHI_PORT:-8011}"
"$python_bin" - "$local_port" <<'PY'
import socket, sys
try:
    port = int(sys.argv[1])
    if not 1024 <= port <= 65535:
        raise ValueError
except ValueError:
    raise SystemExit("NYAYSAATHI_PORT must be a number from 1024 to 65535.")
with socket.socket() as listener:
    try:
        listener.bind(("127.0.0.1", port))
    except OSError:
        raise SystemExit(f"Port {port} is busy. Stop the existing app or set NYAYSAATHI_PORT to another port.")
PY

echo "Starting NyaySaathi on this Mac. Safari will open after its health check."
echo "Use fictional details only. Verified law remains gated."
echo "Live AI requires GEMINI_API_KEY and GEMINI_TERMS_REVIEWED configured locally."
echo "Keep this Terminal open; press Control-C to stop the app."
"$python_bin" -m scripts.run_demo --port "$local_port" &
server_pid=$!
trap 'kill "$server_pid" 2>/dev/null || true' EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

"$python_bin" - "$local_port" "$server_pid" <<'PY'
import json, os, subprocess, sys, time, urllib.request

port, pid = int(sys.argv[1]), int(sys.argv[2])
url = f"http://127.0.0.1:{port}"
for _ in range(180):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        raise SystemExit("The server stopped before becoming ready. Review the error above.")
    try:
        with urllib.request.urlopen(url + "/api/health", timeout=2) as response:
            health = json.load(response)
        if health.get("status") == "ok" and health.get("database") == "sqlite-fts5" and health.get("demo_only") is True:
            subprocess.run(["open", "-a", "Safari", url], check=True)
            print("Ready in Safari: " + url)
            break
    except (OSError, ValueError):
        pass
    time.sleep(1)
else:
    raise SystemExit("The server did not become ready within the startup window. Review the Terminal output.")
PY
wait "$server_pid"
