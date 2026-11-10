# Start (or resume) a training run as its own hidden process, so it keeps going when VS Code or the
# chat is closed. Output is appended to <project>\<name>\train.log. Arguments after -Name are passed
# to ml\train_run.py unchanged.
#   powershell -ExecutionPolicy Bypass -File tools\start_training.ps1 -Project runs\teacher -Name teacher `
#       --data data/rdd2022/teacher/data.yaml --imgsz 960 --batch 6 --epochs 30 --patience 8
# Re-running the same line after a crash resumes from last.pt (never from scratch).
param(
    [Parameter(Mandatory = $true)][string]$Project,
    [Parameter(Mandatory = $true)][string]$Name,
    [Parameter(ValueFromRemainingArguments = $true)][string[]]$Rest
)
$root = Split-Path -Parent $PSScriptRoot
$run = Join-Path $root (Join-Path $Project $Name)
New-Item -ItemType Directory -Force -Path $run | Out-Null
$log = Join-Path $run "train.log"
$py = Join-Path $root ".venv\Scripts\python.exe"
$argsLine = ($Rest | ForEach-Object { if ($_ -match '\s') { "`"$_`"" } else { $_ } }) -join ' '
$cmd = "cd /d `"$root`" && set `"PYTHONUTF8=1`" && `"$py`" -u ml\train_run.py --project $Project --name $Name $argsLine >> `"$log`" 2>&1"
Add-Content -Path $log -Value "`r`n===== $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') start_training: $Project\$Name $argsLine"
$p = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", $cmd -WindowStyle Hidden -PassThru
"Started $Project\$Name (process $($p.Id)). Log: $log"
