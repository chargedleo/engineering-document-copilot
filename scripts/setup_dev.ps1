# PowerShell Development Setup Script
Write-Host "=== Setting up Engineering Document Intelligence & CAD Copilot ===" -ForegroundColor Cyan

# 1. Check for .env file
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
} else {
    Write-Host ".env already exists." -ForegroundColor Green
}

# 2. Check Python
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if ($null -eq $pythonCmd) {
    Write-Host "Python not found in PATH. Please install Python 3.11+." -ForegroundColor Red
} else {
    Write-Host "Found Python: $($pythonCmd.Source)" -ForegroundColor Green
    if (-not (Test-Path "backend\.venv")) {
        Write-Host "Creating backend virtual environment..." -ForegroundColor Yellow
        python -m venv backend\.venv
        Write-Host "To activate: .\backend\.venv\Scripts\Activate.ps1" -ForegroundColor Cyan
    }
}

# 3. Check Node.js
$nodeCmd = Get-Command node -ErrorAction SilentlyContinue
if ($null -eq $nodeCmd) {
    Write-Host "Node.js not found in PATH. Please install Node.js 18+." -ForegroundColor Red
} else {
    Write-Host "Found Node.js: $($nodeCmd.Source)" -ForegroundColor Green
}

Write-Host "=== Setup check complete! ===" -ForegroundColor Cyan
