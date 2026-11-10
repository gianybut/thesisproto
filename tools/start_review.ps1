# Start (or restart) the label review tool as its own hidden process, so it keeps running when
# VS Code or the chat is closed. Output: data\local\logs\review_server.log.
#   powershell -ExecutionPolicy Bypass -File tools\start_review.ps1          # this computer only
#   powershell -ExecutionPolicy Bypass -File tools\start_review.ps1 -Lan     # other laptops on the same Wi-Fi
param([switch]$Lan)
$root = Split-Path -Parent $PSScriptRoot
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
    Where-Object { $_.CommandLine -like '*review_labels*server.py*' } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Start-Sleep 1
New-Item -ItemType Directory -Force -Path (Join-Path $root "data\local\logs") | Out-Null
$py = Join-Path $root ".venv\Scripts\python.exe"
$log = Join-Path $root "data\local\logs\review_server.log"
$lanArg = if ($Lan) { " --lan" } else { "" }
$cmd = "cd /d `"$root`" && set `"PYTHONUTF8=1`" && `"$py`" -u tools\review_labels\server.py$lanArg > `"$log`" 2>&1"
$p = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", $cmd -WindowStyle Hidden -PassThru
Start-Sleep 3
Get-Content $log
