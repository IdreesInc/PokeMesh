#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

MGBA_BIN="$SCRIPT_DIR/mgba/mGBA.app/Contents/MacOS/mGBA"
MGBA_HTTP="$SCRIPT_DIR/mgba/mGBA-http-0.8.2-osx-arm64-self-contained"
LUA_SCRIPT="$SCRIPT_DIR/mgba/mGBASocketServer.lua"
ROM="$SCRIPT_DIR/data/firered.gba"

if [[ -z "$ROM" ]]; then
  echo "Error: 'rom' not set in secrets.json"
  exit 1
fi

if [[ ! -f "$ROM" ]]; then
  echo "Error: ROM not found at: $ROM"
  exit 1
fi

echo "Starting mGBA HTTP server..."
"$MGBA_HTTP" &
MGBA_HTTP_PID=$!

echo "Launching mGBA with ROM: $ROM"
"$MGBA_BIN" --script "$LUA_SCRIPT" "$ROM" &
MGBA_PID=$!

cleanup() {
  kill $MGBA_HTTP_PID $MGBA_PID 2>/dev/null || true
  kill -9 $(lsof -ti:5000) 2>/dev/null || true
}
trap "cleanup; exit" INT TERM EXIT

echo "mGBA HTTP PID: $MGBA_HTTP_PID"
echo "mGBA PID:      $MGBA_PID"
echo "Press Ctrl+C to stop both."

wait $MGBA_PID
