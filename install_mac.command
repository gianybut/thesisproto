#!/bin/bash
# OcuLubak installer for macOS. Double-click this file in Finder.
#
# It sets up the project once (Python packages in .venv, website packages in
# frontend/node_modules), then creates two apps in your Applications folder:
#   OcuLubak       starts the server and the website in the background and opens the browser
#   Stop OcuLubak  stops them
# Run it again after moving the project folder, or after pulling changes to requirements.txt
# or frontend/package.json. Nothing outside this folder and ~/Applications is changed, except
# the Dock if you say yes to that.

set -u
REPO="$(cd "$(dirname "$0")" && pwd)"
RUN="$REPO/.oculubak"
APPS="$HOME/Applications"
cd "$REPO" || exit 1

bold() { printf '\n\033[1m%s\033[0m\n' "$1"; }
ok()   { printf '  \033[32m✓\033[0m %s\n' "$1"; }
warn() { printf '  \033[33m!\033[0m %s\n' "$1"; }
fail() { printf '\n  \033[31m✗ %s\033[0m\n\n' "$1"; read -r -p "Press Return to close." _; exit 1; }
ask()  { local a; read -r -p "  $1 [Y/n] " a; [ -z "$a" ] || [[ "$a" =~ ^[Yy] ]]; }

# Homebrew and the official Node installer put tools here; a Finder-opened Terminal may not.
export PATH="$PATH:/opt/homebrew/bin:/usr/local/bin"

echo
echo "  OcuLubak installer for macOS"
echo "  Project folder: $REPO"

# ---------------------------------------------------------------- 1. Tools
bold "1. Checking the tools OcuLubak needs"

if [ -x .venv/bin/python ]; then
  ok "Python environment found ($(.venv/bin/python --version 2>&1))"
else
  PYTHON=""
  for cand in python3.12 python3.11 python3.10 python3.13 python3; do
    if command -v "$cand" >/dev/null 2>&1; then PYTHON="$(command -v "$cand")"; break; fi
  done
  [ -n "$PYTHON" ] || fail "Python 3 is not installed. Install it from python.org (3.10 to 3.12), then run this installer again."
  ok "Python found: $PYTHON ($("$PYTHON" --version 2>&1))"
fi

command -v node >/dev/null 2>&1 || fail "Node.js is not installed. Install the LTS version from nodejs.org, then run this installer again."
NODE_MAJOR="$(node -p 'process.versions.node.split(".")[0]')"
[ "$NODE_MAJOR" -ge 20 ] || fail "Node.js $(node --version) is too old. Install version 20 or newer from nodejs.org."
ok "Node.js $(node --version)"

if command -v ffmpeg >/dev/null 2>&1; then
  ok "ffmpeg found"
else
  warn "ffmpeg is not installed. OcuLubak runs without it, but annotated videos will not play in the browser."
  warn "Install it with:  brew install ffmpeg"
fi

# ---------------------------------------------------------------- 2. Packages
bold "2. Installing packages (the first time can take 10 minutes or more)"

if [ ! -x .venv/bin/python ]; then
  "$PYTHON" -m venv .venv || fail "Could not create the Python environment (.venv)."
  ok "Created the Python environment"
fi
.venv/bin/python -m pip install --upgrade pip --quiet || warn "Could not update pip; continuing."
.venv/bin/python -m pip install -r requirements.txt || fail "Installing the Python packages failed. Check your internet connection and run this installer again."
ok "Python packages installed"

(cd frontend && npm install --no-fund --no-audit) || fail "Installing the website packages failed. Check your internet connection and run this installer again."
ok "Website packages installed"

mkdir -p "$RUN"
# The apps are opened from Finder with a bare PATH, so remember where node is.
printf 'NODE_DIR=%q\n' "$(dirname "$(command -v node)")" >"$RUN/paths.sh"
chmod +x launcher/mac/launch.sh launcher/mac/stop.sh

# ---------------------------------------------------------------- 3. Apps
bold "3. Creating the OcuLubak apps in $APPS"

make_app() {   # <name> <script> <bundle id>
  # An AppleScript applet: macOS will not launch a bundle whose executable is a bare shell
  # script, but an applet is a real app that runs our script and quits.
  local app="$APPS/$1.app" plist
  rm -rf "$app"
  osacompile -o "$app" -e "do shell script quoted form of \"$REPO/launcher/mac/$2\"" \
    || fail "Could not create $1.app."
  plist="$app/Contents/Info.plist"
  cp launcher/oculubak.icns "$app/Contents/Resources/applet.icns"
  /usr/libexec/PlistBuddy -c "Set :CFBundleIdentifier $3" "$plist" 2>/dev/null \
    || /usr/libexec/PlistBuddy -c "Add :CFBundleIdentifier string $3" "$plist"
  # Starts the servers and quits: no Dock icon bouncing while they come up.
  /usr/libexec/PlistBuddy -c "Add :LSUIElement bool true" "$plist" 2>/dev/null \
    || /usr/libexec/PlistBuddy -c "Set :LSUIElement true" "$plist"
  # Changing the icon and Info.plist breaks the applet's signature; sign it again (ad hoc).
  codesign --force --deep --sign - "$app" >/dev/null 2>&1 || warn "Could not re-sign $1.app; it may not open."
  # Make Finder pick up the icon straight away.
  /System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -f "$app" >/dev/null 2>&1
  touch "$app"
  ok "$1.app"
}

mkdir -p "$APPS"
make_app "OcuLubak" "launch.sh" "local.oculubak.launcher"
make_app "Stop OcuLubak" "stop.sh" "local.oculubak.stop"

if ask "Add OcuLubak to the Dock?"; then
  if defaults read com.apple.dock persistent-apps 2>/dev/null | grep -q "OcuLubak.app"; then
    ok "OcuLubak is already in the Dock"
  else
    defaults write com.apple.dock persistent-apps -array-add \
      "<dict><key>tile-data</key><dict><key>file-data</key><dict><key>_CFURLString</key><string>file://$APPS/OcuLubak.app/</string><key>_CFURLStringType</key><integer>15</integer></dict></dict></dict>"
    killall Dock
    ok "Added to the Dock"
  fi
fi

bold "Done"
echo "  Open OcuLubak from the Dock, Launchpad, Spotlight (⌘ Space, type OcuLubak) or $APPS."
echo "  It opens http://localhost:5173 in your browser. Sign in as admin / admin123 the first time,"
echo "  then change that password."
echo "  To shut it down, open \"Stop OcuLubak\". Logs are in $RUN."
echo

if ask "Open OcuLubak now?"; then
  open "$APPS/OcuLubak.app"
fi
echo
read -r -p "Press Return to close." _
