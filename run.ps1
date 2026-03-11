# Run from repository root: powershell -ExecutionPolicy Bypass -File .\run.ps1
$ErrorActionPreference = 'Stop'

if (Get-Command py -ErrorAction SilentlyContinue) {
  py app.py
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
  python app.py
} else {
  Write-Host 'Python was not found. Please install Python from https://python.org and rerun.' -ForegroundColor Red
  exit 1
}
