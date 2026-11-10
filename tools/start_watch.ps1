# Start tools\watch_training.py as its own hidden process (keeps running when VS Code is closed).
# Does nothing if a watcher is already running. Output: runs\watch_training.log.
$root = Split-Path -Parent $PSScriptRoot
$running = Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -like '*watch_training.py*' }
if ($running) { "Watcher already running (process $($running[0].ProcessId))."; exit 0 }
New-Item -ItemType Directory -Force -Path (Join-Path $root "runs") | Out-Null
$py = Join-Path $root ".venv\Scripts\python.exe"
$log = Join-Path $root "runs\watch_training.log"
$cmd = "cd /d `"$root`" && set `"PYTHONUTF8=1`" && `"$py`" -u tools\watch_training.py >> `"$log`" 2>&1"
$p = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", $cmd -WindowStyle Hidden -PassThru
"Watcher started (process $($p.Id)). Status: results\training_status.md"
