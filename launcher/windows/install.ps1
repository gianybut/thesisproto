# OcuLubak installer for Windows (run by install_windows.bat in the project folder).
#
# Sets up the project once (Python packages in .venv, website packages in
# frontend\node_modules) and creates shortcuts:
#   Desktop and Start menu:  OcuLubak       starts the server and website hidden, opens the browser
#   Start menu:              Stop OcuLubak  stops them
# Run it again after moving the project folder, or after pulling changes to requirements.txt
# or frontend\package.json. Written for Windows PowerShell 5.1 (built into Windows 10 and 11).

# Continue, not Stop: in Windows PowerShell 5.1 a native tool writing progress to stderr would
# otherwise abort the script. Every step checks $LASTEXITCODE or the result itself.
$ErrorActionPreference = 'Continue'
$Repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$Run = Join-Path $Repo '.oculubak'
Set-Location $Repo

function Step($text) { Write-Host ''; Write-Host $text -ForegroundColor White }
function Ok($text)   { Write-Host "  [ok] $text" -ForegroundColor Green }
function Warn($text) { Write-Host "  [!]  $text" -ForegroundColor Yellow }
function Fail($text) { Write-Host ''; Write-Host "  [x]  $text" -ForegroundColor Red; exit 1 }
function Ask($text) {
  $a = Read-Host "  $text [Y/n]"
  return ($a -eq '' -or $a -match '^[Yy]')
}
function Have($cmd) { return [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }

Write-Host ''
Write-Host '  OcuLubak installer for Windows'
Write-Host "  Project folder: $Repo"

# ---------------------------------------------------------------- 1. Tools
Step '1. Checking the tools OcuLubak needs'

$VenvPy = Join-Path $Repo '.venv\Scripts\python.exe'
$PyExe = $null      # the Python used to create .venv
$PyArgs = @()       # e.g. -3.12 for the py launcher
if (Test-Path $VenvPy) {
  Ok "Python environment found ($(& $VenvPy --version))"
} else {
  # Prefer the py launcher (python.org installer). A bare "python" may be the Microsoft Store stub.
  if (Have 'py') {
    foreach ($v in '3.12', '3.11', '3.10') {
      $null = & py "-$v" --version 2>$null
      if ($LASTEXITCODE -eq 0) { $PyExe = 'py'; $PyArgs = @("-$v"); break }
    }
  }
  if (-not $PyExe -and (Have 'python')) {
    $out = & python --version 2>$null
    if ($LASTEXITCODE -eq 0 -and "$out" -match 'Python 3\.1[0-2]') { $PyExe = 'python' }
  }
  if (-not $PyExe) { Fail 'Python 3.10 to 3.12 is not installed. Install it from python.org (tick "Add python.exe to PATH"), then run this installer again.' }
  Ok "Python found ($(& $PyExe @PyArgs --version))"
}

if (-not (Have 'node')) { Fail 'Node.js is not installed. Install the LTS version from nodejs.org, then run this installer again.' }
$nodeMajor = [int]((& node -p "process.versions.node.split('.')[0]") | Out-String).Trim()
if ($nodeMajor -lt 20) { Fail "Node.js $(& node --version) is too old. Install version 20 or newer from nodejs.org." }
Ok "Node.js $(& node --version)"

if (Have 'ffmpeg') { Ok 'ffmpeg found' }
else {
  Warn 'ffmpeg is not installed. OcuLubak runs without it, but annotated videos will not play in the browser.'
  Warn 'Install it with:  winget install Gyan.FFmpeg'
}

if (-not (Have 'curl.exe')) { Fail 'curl.exe was not found. It comes with Windows 10 (1803) and later; update Windows, then try again.' }

# ---------------------------------------------------------------- 2. Packages
Step '2. Installing packages (the first time can take 10 minutes or more)'

if (-not (Test-Path $VenvPy)) {
  & $PyExe @PyArgs -m venv .venv
  if ($LASTEXITCODE -ne 0 -or -not (Test-Path $VenvPy)) { Fail 'Could not create the Python environment (.venv).' }
  Ok 'Created the Python environment'
}
$env:PYTHONUTF8 = '1'
& $VenvPy -m pip install --upgrade pip --quiet
& $VenvPy -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { Fail 'Installing the Python packages failed. Check your internet connection and run this installer again.' }
Ok 'Python packages installed'

Push-Location (Join-Path $Repo 'frontend')
& npm.cmd install --no-fund --no-audit
$npmExit = $LASTEXITCODE
Pop-Location
if ($npmExit -ne 0) { Fail 'Installing the website packages failed. Check your internet connection and run this installer again.' }
Ok 'Website packages installed'

# The model weights (ml\models\*.pt) are stored with Git LFS. A clone made without Git LFS has
# 130-byte text placeholders instead, and every survey analysis then fails at 0%.
function Is-Placeholder($path) {
  $bytes = Get-Content -Path $path -Encoding Byte -TotalCount 40 -ErrorAction SilentlyContinue
  return ($bytes -and ([System.Text.Encoding]::ASCII.GetString($bytes) -match 'git-lfs'))
}
$models = Get-ChildItem (Join-Path $Repo 'ml\models\*.pt') -ErrorAction SilentlyContinue
if ($models | Where-Object { Is-Placeholder $_.FullName }) {
  $null = & git lfs version 2>$null
  if ($LASTEXITCODE -ne 0) { Fail 'The detection model needs Git LFS to download. Install Git for Windows (it includes Git LFS) or run: winget install GitHub.GitLFS. Then run this installer again.' }
  & git lfs install --local | Out-Null
  & git lfs pull --include "ml/models/*.pt"
  if ($LASTEXITCODE -ne 0) { Fail "Could not download the detection model. Check your internet connection and access to the project's GitHub repository, then run this installer again." }
  foreach ($m in $models) { if (Is-Placeholder $m.FullName) { Fail "$($m.Name) is still a placeholder after downloading. Ask the team for the model file." } }
}
Ok 'Detection model present'

# The AI check model (CLIP, ~570 MB) is fetched from Hugging Face once, so analysis works offline.
# Not fatal: without it surveys are still analysed and records are left "not checked".
$env:PYTHONUTF8 = '1'
& $VenvPy backend\services\damage_verifier.py --download *> $null
if ($LASTEXITCODE -eq 0) { Ok 'AI check model present' }
else { Warn 'Could not download the AI check model. Surveys still work; run this installer again with internet to add it.' }

New-Item -ItemType Directory -Force -Path $Run | Out-Null

# ---------------------------------------------------------------- 3. Shortcuts
Step '3. Creating the OcuLubak shortcuts'

$shell = New-Object -ComObject WScript.Shell
$vbs = Join-Path $Repo 'launcher\windows\OcuLubak.vbs'
$icon = Join-Path $Repo 'launcher\oculubak.ico'
$startMenu = Join-Path ([Environment]::GetFolderPath('Programs')) 'OcuLubak'
New-Item -ItemType Directory -Force -Path $startMenu | Out-Null

function Make-Shortcut($path, $arguments, $description) {
  $s = $shell.CreateShortcut($path)
  $s.TargetPath = Join-Path $env:WINDIR 'System32\wscript.exe'
  $s.Arguments = "`"$vbs`" $arguments"
  $s.WorkingDirectory = $Repo
  $s.IconLocation = "$icon,0"
  $s.Description = $description
  $s.Save()
}

Make-Shortcut (Join-Path $startMenu 'OcuLubak.lnk') 'start' 'Start OcuLubak and open it in the browser'
Make-Shortcut (Join-Path $startMenu 'Stop OcuLubak.lnk') 'stop' 'Stop the OcuLubak server and website'
Ok 'Start menu: OcuLubak, Stop OcuLubak'

$desktop = [Environment]::GetFolderPath('Desktop')
if (Ask 'Put an OcuLubak shortcut on the Desktop?') {
  Make-Shortcut (Join-Path $desktop 'OcuLubak.lnk') 'start' 'Start OcuLubak and open it in the browser'
  Ok 'Desktop: OcuLubak'
}

Step 'Done'
Write-Host '  Open OcuLubak from the Desktop or the Start menu. It opens http://localhost:5173 in your browser.'
Write-Host '  Sign in as admin / admin123 the first time, then change that password.'
Write-Host "  To shut it down, open Stop OcuLubak from the Start menu. Logs are in $Run."
Write-Host '  The first start may show a Windows Firewall prompt for Python: allow it on private networks,'
Write-Host '  so phones on the same Wi-Fi can upload surveys.'
Write-Host ''

if (Ask 'Open OcuLubak now?') {
  Start-Process -FilePath (Join-Path $env:WINDIR 'System32\wscript.exe') -ArgumentList "`"$vbs`" start"
}
