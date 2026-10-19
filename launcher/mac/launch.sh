#!/bin/bash
# Start OcuLubak (backend on :5000, website on :5173) in the background and open it in the
# browser. Run by the OcuLubak app that install_mac.command puts in ~/Applications; safe to
# run again while it is running (it then only opens the browser).
#
# Logs and process ids go to <repo>/.oculubak/. Stop it with "Stop OcuLubak" (stop.sh).

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
RUN="$REPO/.oculubak"
mkdir -p "$RUN"

# An app opened from Finder gets a bare PATH. The installer records where node lives.
[ -f "$RUN/paths.sh" ] && . "$RUN/paths.sh"
export PATH="${NODE_DIR:+$NODE_DIR:}$PATH:/opt/homebrew/bin:/usr/local/bin"

PY="$REPO/.venv/bin/python"
URL="http://localhost:5173"
export PYTHONUTF8=1   # the backend logs with emoji

say() {   # dialog with an optional "Show log" button
  local msg="$1" log="$2"
  if [ -n "$log" ]; then
    local pick
    pick=$(osascript -e "button returned of (display dialog \"$msg\" with title \"OcuLubak\" buttons {\"Show log\", \"OK\"} default button \"OK\" with icon caution)" 2>/dev/null)
    [ "$pick" = "Show log" ] && open -R "$log"
  else
    osascript -e "display dialog \"$msg\" with title \"OcuLubak\" buttons {\"OK\"} default button \"OK\" with icon caution" >/dev/null 2>&1
  fi
}
notify() { osascript -e "display notification \"$1\" with title \"OcuLubak\"" >/dev/null 2>&1; }

http_code() { curl -s -o /dev/null -w '%{http_code}' --max-time 2 "$1" 2>/dev/null; }
# The backend answers 401 to an unsigned /api/auth/me; anything else on :5000 is another program.
backend_up() { [ "$(http_code http://127.0.0.1:5000/api/auth/me)" = "401" ]; }
frontend_up() { [ "$(http_code "$URL/")" = "200" ]; }
port_taken() { lsof -nP -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1; }

# Start a command in its own process group, so stop.sh can end it and its children together.
start_detached() {   # <log> <pidfile> <dir> <command...>
  local log="$1" pidfile="$2" dir="$3"; shift 3
  ( cd "$dir" && nohup "$PY" -c 'import os, sys; os.setsid(); os.execvp(sys.argv[1], sys.argv[1:])' "$@" >>"$log" 2>&1 &
    echo $! >"$pidfile" )
}

if [ ! -x "$PY" ] || [ ! -d "$REPO/frontend/node_modules" ]; then
  say "OcuLubak is not set up on this Mac yet. Double-click install_mac.command in the project folder first."
  exit 1
fi

if backend_up && frontend_up; then
  open "$URL"
  exit 0
fi

notify "Starting OcuLubak…"

if ! backend_up; then
  if port_taken 5000; then
    say "Another program is using port 5000, which OcuLubak needs. On a Mac this is usually AirPlay Receiver: turn it off in System Settings › General › AirDrop & Handoff, then open OcuLubak again."
    exit 1
  fi
  echo "=== $(date) starting backend" >>"$RUN/backend.log"
  start_detached "$RUN/backend.log" "$RUN/backend.pid" "$REPO/backend" "$PY" run.py
fi

if ! frontend_up; then
  if port_taken 5173; then
    say "Another program is using port 5173, which the OcuLubak website needs. Quit it (or run Stop OcuLubak), then open OcuLubak again."
    exit 1
  fi
  if ! command -v npm >/dev/null 2>&1; then
    say "Node.js was not found. Install it from nodejs.org, then run install_mac.command again."
    exit 1
  fi
  echo "=== $(date) starting website" >>"$RUN/frontend.log"
  start_detached "$RUN/frontend.log" "$RUN/frontend.pid" "$REPO/frontend" "$(command -v npm)" run dev -- --strictPort
fi

# First start after a pull can take a while (the backend migrates the database).
for _ in $(seq 1 90); do
  if backend_up && frontend_up; then
    open "$URL"
    exit 0
  fi
  sleep 1
done

if ! backend_up; then
  say "The OcuLubak server did not start within 90 seconds." "$RUN/backend.log"
else
  say "The OcuLubak website did not start within 90 seconds." "$RUN/frontend.log"
fi
exit 1
