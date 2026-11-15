# Start (or restart) the damage log review page as its own hidden process, then open it in the browser.
# Output: results\damage_log_check\review_server.log
#   powershell -ExecutionPolicy Bypass -File tools\start_damage_review.ps1
$root = Split-Path -Parent $PSScriptRoot
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
    Where-Object { $_.CommandLine -like '*review_damage_log*server.py*' } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Start-Sleep 1
$py = Join-Path $root ".venv\Scripts\python.exe"
$log = Join-Path $root "results\damage_log_check\review_server.log"
$cmd = "cd /d `"$root`" && set `"PYTHONUTF8=1`" && `"$py`" -u tools\review_damage_log\server.py --no-browser > `"$log`" 2>&1"
Start-Process -FilePath "cmd.exe" -ArgumentList "/c", $cmd -WindowStyle Hidden | Out-Null
Start-Sleep 4
Get-Content $log
Start-Process "http://127.0.0.1:8771"
