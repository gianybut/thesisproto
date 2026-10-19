# Stop OcuLubak: the backend and website started by launch.ps1 (with their child processes),
# plus anything of this project's still listening on :5000 / :5173.

$ErrorActionPreference = 'Continue'
$Repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$Run = Join-Path $Repo '.oculubak'
$stopped = $false

foreach ($name in 'backend', 'frontend') {
  $pidFile = Join-Path $Run "$name.pid"
  if (-not (Test-Path $pidFile)) { continue }
  $procId = (Get-Content $pidFile | Select-Object -First 1).Trim()
  if ($procId -and (Get-Process -Id $procId -ErrorAction SilentlyContinue)) {
    & taskkill.exe /PID $procId /T /F *> $null   # /T: the Flask reloader child and node too
    $stopped = $true
  }
  Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
}

# Anything else of this project's on the two ports (for example started by hand). Only
# processes running from inside the project folder are touched.
foreach ($port in 5000, 5173) {
  $owners = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique
  foreach ($procId in $owners) {
    $cmd = (Get-CimInstance Win32_Process -Filter "ProcessId = $procId" -ErrorAction SilentlyContinue).CommandLine
    $exe = (Get-Process -Id $procId -ErrorAction SilentlyContinue).Path
    # A venv's python.exe hands over to the base interpreter, whose command line is just
    # "python.exe run.py", so the backend's own script name counts as a match too.
    if (("$cmd" -like "*$Repo*") -or ("$exe" -like "$Repo*") -or ("$cmd" -match 'run\.py|vite')) {
      & taskkill.exe /PID $procId /T /F *> $null
      $stopped = $true
    }
  }
}

Add-Type -AssemblyName System.Windows.Forms
$msg = if ($stopped) { 'OcuLubak has stopped.' } else { 'OcuLubak was not running.' }
[System.Windows.Forms.MessageBox]::Show($msg, 'OcuLubak', 'OK', 'Information') | Out-Null
