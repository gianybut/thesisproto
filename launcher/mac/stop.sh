#!/bin/bash
# Stop OcuLubak: the backend and the website started by launch.sh, plus anything of this
# project's still listening on :5000 / :5173 (for example a server started by hand).

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
RUN="$REPO/.oculubak"
stopped=0

# Processes launch.sh started lead their own process group: end the whole group.
for name in backend frontend; do
  pidfile="$RUN/$name.pid"
  [ -f "$pidfile" ] || continue
  pid=$(cat "$pidfile")
  if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
    kill -TERM -"$pid" 2>/dev/null || kill -TERM "$pid" 2>/dev/null
    stopped=1
  fi
  rm -f "$pidfile"
done

# Anything else of this project's on the two ports. Only processes whose working folder is in
# the project are touched, so an unrelated program on the same port is left alone.
for port in 5000 5173; do
  for pid in $(lsof -nP -t -iTCP:"$port" -sTCP:LISTEN 2>/dev/null); do
    cwd=$(lsof -a -p "$pid" -d cwd -Fn 2>/dev/null | sed -n 's/^n//p')
    case "$cwd" in
      "$REPO"*) kill -TERM "$pid" 2>/dev/null && stopped=1 ;;
    esac
  done
done

sleep 1
if [ "$stopped" = 1 ]; then
  osascript -e 'display notification "OcuLubak has stopped." with title "OcuLubak"' >/dev/null 2>&1
else
  osascript -e 'display notification "OcuLubak was not running." with title "OcuLubak"' >/dev/null 2>&1
fi
