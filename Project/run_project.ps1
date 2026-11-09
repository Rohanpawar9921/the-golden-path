param(
    [switch]$SkipKnowledgeIndex,
    [switch]$SkipModelTraining,
    [switch]$StartDashboard
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $projectRoot

if (Test-Path -LiteralPath ".venv\Scripts\python.exe") {
    $python = (Resolve-Path ".venv\Scripts\python.exe").Path
} else {
    $python = "python"
}

function Invoke-ProjectStep {
    param(
        [string]$Label,
        [string[]]$Arguments
    )

    Write-Host "`n=== $Label ===" -ForegroundColor Cyan
    & $python @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Label failed with exit code $LASTEXITCODE."
    }
}

Invoke-ProjectStep "Cleaning datasets" @("run_data_pipeline.py")

if (-not $SkipKnowledgeIndex) {
    Invoke-ProjectStep "Building knowledge index" @("run_knowledge_indexing.py")
}

if (-not $SkipModelTraining) {
    Invoke-ProjectStep "Training models" @("run_model_training.py")
}

Invoke-ProjectStep "Setting up database" @("run_database_setup.py")

if ($StartDashboard) {
    Write-Host "`nStarting dashboard in a separate process..." -ForegroundColor Cyan
    Start-Process -FilePath $python -ArgumentList "-m", "streamlit", "run", "dashboard/clearance_queue.py" -WorkingDirectory $projectRoot
}

Write-Host "`nStarting API at http://127.0.0.1:8000" -ForegroundColor Green
& $python -m uvicorn api.routes:service_application --host 127.0.0.1 --port 8000
if ($LASTEXITCODE -ne 0) {
    throw "API service failed with exit code $LASTEXITCODE."
}
