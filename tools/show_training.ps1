# Live view of a training run, for the team: which run is going, its latest progress line, and the GPU.
#   powershell -ExecutionPolicy Bypass -File tools\show_training.ps1                 # Step 0 benchmark
#   powershell -ExecutionPolicy Bypass -File tools\show_training.ps1 -Runs runs\step4
#   powershell -ExecutionPolicy Bypass -File tools\show_training.ps1 -Runs data\local\logs -Filter *.log
# Works in the VS Code terminal too (Ctrl+`). Read-only: stopping it (Ctrl+C) does not stop the job.
param([string]$Runs = "runs\step0", [int]$Seconds = 3, [string]$Filter = "train.log")
$root = Split-Path -Parent $PSScriptRoot
$dir = Join-Path $root $Runs
$host.UI.RawUI.WindowTitle = "OcuLubak training - $Runs"

# Training keeps its log open for writing, so open it shared (a plain read is refused) and take the end only.
function Read-Tail([string]$path, [int]$bytes = 16384) {
    $fs = [IO.File]::Open($path, 'Open', 'Read', 'ReadWrite, Delete')
    try {
        $start = [Math]::Max(0, $fs.Length - $bytes)
        $null = $fs.Seek($start, 'Begin')
        $buf = New-Object byte[] ($fs.Length - $start)
        $n = $fs.Read($buf, 0, $buf.Length)
        return [Text.Encoding]::UTF8.GetString($buf, 0, $n)
    } finally { $fs.Close() }
}

while ($true) {
  try {
    $out = @("OcuLubak training view  ($(Get-Date -Format 'HH:mm:ss'))   folder: $Runs   (close this window any time)", "")
    $driver = Join-Path $dir "driver.log"
    if (Test-Path $driver) { $out += "--- runs so far ---"; $out += Get-Content $driver -Tail 12; $out += "" }
    $log = Get-ChildItem -Path $dir -Recurse -Filter $Filter -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($log) {
        $out += "--- latest output: $($log.Directory.Name)\$($log.Name) ---"
        $text = (Read-Tail $log.FullName) -replace "$([char]27)\[[0-9;]*[A-Za-z]", ""
        $lines = $text -split "[`r`n]+" | Where-Object { $_.Trim() -ne "" }
        $out += $lines | Select-Object -Last 8
        $out += ""
    }
    $gpu = & nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader,nounits
    if ($gpu) {
        $g = $gpu.Split(",") | ForEach-Object { $_.Trim() }
        $out += "--- GPU: $($g[0])% busy, $($g[1]) / $($g[2]) MiB memory, $($g[3]) C ---"
    }
    Clear-Host
    $out | ForEach-Object { Write-Host $_ }
  } catch {
    Write-Host "(view could not refresh: $($_.Exception.Message); retrying)" -ForegroundColor Yellow
  }
    Start-Sleep -Seconds $Seconds
}
