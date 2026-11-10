# Start tools\pipeline_v2.py as its own hidden process (keeps running when VS Code is closed).
# Does nothing if it is already running. Log: runs\v2\pipeline.log; status: results\pipeline_status.md.
$root = Split-Path -Parent $PSScriptRoot
$running = Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -like '*pipeline_v2.py*' }
if ($running) { "Pipeline already running (process $($running[0].ProcessId))."; exit 0 }
New-Item -ItemType Directory -Force -Path (Join-Path $root "runs\v2") | Out-Null
$py = Join-Path $root ".venv\Scripts\python.exe"
$out = Join-Path $root "runs\v2\pipeline_console.log"
$cmd = "cd /d `"$root`" && set `"PYTHONUTF8=1`" && `"$py`" -u tools\pipeline_v2.py >> `"$out`" 2>&1"
$p = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", $cmd -WindowStyle Hidden -PassThru
"Pipeline started (process $($p.Id)). Status: results\pipeline_status.md"
