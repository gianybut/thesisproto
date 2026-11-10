@echo off
REM Team labelling site: annotation server (with its 30-min backup job) + Cloudflare tunnel.
REM Double-click, or run from the repo root:  tools\start_labeling.bat
REM Needs ANNOTATE_PASSCODE in .env at the repo root (see .env.example) and cloudflared
REM (winget install --id Cloudflare.cloudflared). Keep this window open and the PC awake.
REM The https://....trycloudflare.com link changes every time this starts: post the new one in the GC.

cd /d "%~dp0.."
if not exist .env (
  echo Missing .env: copy .env.example to .env and set ANNOTATE_PASSCODE.
  pause & exit /b 1
)
where cloudflared >nul 2>nul || (
  echo cloudflared not found. Install it:  winget install --id Cloudflare.cloudflared
  echo then open a new window and start this again.
  pause & exit /b 1
)

REM Never sleep on AC power while the site is up (restore later with: powercfg /change standby-timeout-ac 30)
powercfg /change standby-timeout-ac 0

echo Starting the annotation server in its own window (port 8771)...
start "Labelling server" cmd /k "set PYTHONUTF8=1&& .venv\Scripts\python.exe tools\review_labels\annotate.py --port 8771"
timeout /t 3 /nobreak >nul

echo.
echo Opening the tunnel. Share the https://....trycloudflare.com link it prints, plus the passcode.
echo Progress page: <link>/stats      Local: http://127.0.0.1:8771
echo.
cloudflared tunnel --url http://localhost:8771
