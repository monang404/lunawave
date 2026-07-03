param (
    [Parameter(Mandatory=$true)]
    [string]$Target
)

Write-Host "Creating backup of current config to cache/backups/ ..."
$timestamp = (Get-Date).ToString("yyyyMMdd_HHmmss")
New-Item -ItemType Directory -Force -Path "cache/backups" | Out-Null
if (Test-Path ".env") { Copy-Item ".env" "cache/backups/.env.$timestamp" }
if (Test-Path "config.local.py") { Copy-Item "config.local.py" "cache/backups/config.local.py.$timestamp" }

Write-Host "Rolling back to $Target..."
git checkout $Target

Write-Host "Syncing dependencies..."
python -m pip install -r requirements.txt
python -m pip install -e .

Write-Host "Rollback complete. Note: you may need to manually revert DB schema."
Write-Host "Your config files before rollback were backed up to cache/backups/"
