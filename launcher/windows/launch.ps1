# Start OcuLubak (backend on :5000, website on :5173) hidden in the background and open it in
# the browser. Run by the OcuLubak shortcut through OcuLubak.vbs (no console window). Safe to
# run again while it is running: it then only opens the browser.
# Logs and process ids go to <repo>\.oculubak\. Stop it with the Stop OcuLubak shortcut.

$ErrorActionPreference = 'Continue'
$Repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$Run = Join-Path $Repo '.oculubak'
New-Item -ItemType Directory -Force -Path $Run | Out-Null
$Py = Join-Path $Repo '.venv\Scripts\python.exe'
$Url = 'http://localhost:5173'
$env:PYTHONUTF8 = '1'   # the backend logs with emoji; cp1252 would crash print()

Add-Type -AssemblyName System.Windows.Forms
function Say($text, $log) {
  if ($log) {
    $pick = [System.Windows.Forms.MessageBox]::Show("$text`n`nOpen the log file?", 'OcuLubak', 'YesNo', 'Warning')
    if ($pick -eq 'Yes') { Start-Process notepad.exe -ArgumentList "`"$log`"" }
  } else {
    [System.Windows.Forms.MessageBox]::Show($text, 'OcuLubak', 'OK', 'Warning') | Out-Null
  }
}

function HttpCode($u) {
  $code = & curl.exe -s -o NUL -w '%{http_code}' --max-time 2 $u 2>$null
  return "$code"
}
# The backend answers 401 to an unsigned /api/auth/me; anything else on :5000 is another program.
function BackendUp { return (HttpCode 'http://127.0.0.1:5000/api/auth/me') -eq '401' }
function FrontendUp { return (HttpCode "$Url/") -eq '200' }
function PortTaken($port) {
  return [bool](Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue)
}

if (-not (Test-Path $Py) -or -not (Test-Path (Join-Path $Repo 'frontend\node_modules'))) {
  Say 'OcuLubak is not set up on this computer yet. Double-click install_windows.bat in the project folder first.'
  exit 1
}

if ((BackendUp) -and (FrontendUp)) { Start-Process $Url; exit 0 }

if (-not (BackendUp)) {
  if (PortTaken 5000) {
    Say 'Another program is using port 5000, which OcuLubak needs. Close it (or run Stop OcuLubak), then open OcuLubak again.'
    exit 1
  }
  Add-Content (Join-Path $Run 'backend.log') "=== $(Get-Date) starting backend"
  $p = Start-Process -FilePath $Py -ArgumentList 'run.py' -WorkingDirectory (Join-Path $Repo 'backend') `
    -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput (Join-Path $Run 'backend.out.log') -RedirectStandardError (Join-Path $Run 'backend.log')
  Set-Content (Join-Path $Run 'backend.pid') $p.Id
}

if (-not (FrontendUp)) {
  if (PortTaken 5173) {
    Say 'Another program is using port 5173, which the OcuLubak website needs. Close it (or run Stop OcuLubak), then open OcuLubak again.'
    exit 1
  }
  if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) {
    Say 'Node.js was not found. Install it from nodejs.org, then run install_windows.bat again.'
    exit 1
  }
  $p = Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', 'npm.cmd run dev -- --strictPort' `
    -WorkingDirectory (Join-Path $Repo 'frontend') -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput (Join-Path $Run 'frontend.log') -RedirectStandardError (Join-Path $Run 'frontend.err.log')
  Set-Content (Join-Path $Run 'frontend.pid') $p.Id
}

# First start after a pull can take a while (the backend migrates the database).
for ($i = 0; $i -lt 90; $i++) {
  if ((BackendUp) -and (FrontendUp)) { Start-Process $Url; exit 0 }
  Start-Sleep -Seconds 1
}

if (-not (BackendUp)) { Say 'The OcuLubak server did not start within 90 seconds.' (Join-Path $Run 'backend.log') }
else { Say 'The OcuLubak website did not start within 90 seconds.' (Join-Path $Run 'frontend.err.log') }
exit 1
