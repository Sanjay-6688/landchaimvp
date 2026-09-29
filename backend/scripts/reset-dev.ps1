# DEVELOPMENT ONLY. Removes all application data and starts a fresh local Hardhat chain.
$ErrorActionPreference = "Stop"
$Repo = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Blockchain = Join-Path $Repo "blockchain"
$Backend = Join-Path $Repo "backend"
$EnvFile = Join-Path $Backend ".env"
if (-not (Test-Path $EnvFile)) { throw "Create backend\.env from .env.example first." }
$Vars = @{}
Get-Content $EnvFile | ForEach-Object { if ($_ -match '^\s*([^#=]+)=(.*)$') { $Vars[$matches[1].Trim()] = $matches[2].Trim() } }
if (-not $Vars.POSTGRES_PASSWORD) { throw "Set POSTGRES_PASSWORD in backend\.env." }
$env:PGPASSWORD = $Vars.POSTGRES_PASSWORD
$db = if ($Vars.POSTGRES_DB) { $Vars.POSTGRES_DB } else { "landchain" }
$db = $db.Trim('"')
if ($db -notmatch '^[A-Za-z_][A-Za-z0-9_]*$') { throw "POSTGRES_DB must be a simple PostgreSQL database name." }
$user = if ($Vars.POSTGRES_USER) { $Vars.POSTGRES_USER } else { "postgres" }
$hostName = if ($Vars.POSTGRES_HOST) { $Vars.POSTGRES_HOST } else { "localhost" }
$port = if ($Vars.POSTGRES_PORT) { $Vars.POSTGRES_PORT } else { "5432" }
$psql = (Get-Command psql -ErrorAction Stop).Source
& $psql -h $hostName -p $port -U $user -d postgres -v ON_ERROR_STOP=1 -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='$db' AND pid <> pg_backend_pid();" | Out-Null
& $psql -h $hostName -p $port -U $user -d postgres -v ON_ERROR_STOP=1 -c "DROP DATABASE IF EXISTS `"$db`";" | Out-Null
& $psql -h $hostName -p $port -U $user -d postgres -v ON_ERROR_STOP=1 -c "CREATE DATABASE `"$db`";" | Out-Null
$listener = Get-NetTCPConnection -LocalPort 8545 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
if ($listener) {
    $listeningProcess = Get-CimInstance Win32_Process -Filter "ProcessId = $($listener.OwningProcess)"
    if (-not $listeningProcess.CommandLine -or $listeningProcess.CommandLine -notlike "*$Blockchain*") {
        throw "Port 8545 is used by a process outside this LandChain workspace. Stop that local service yourself before resetting."
    }
    Stop-Process -Id $listener.OwningProcess -Force
}
$npm = Join-Path (Split-Path (Get-Command node -ErrorAction Stop).Source) "npm.cmd"
$nodeProcess = Start-Process -FilePath $npm -ArgumentList @("exec","--","hardhat","node") -WorkingDirectory $Blockchain -WindowStyle Hidden -PassThru
Start-Sleep -Seconds 4
Push-Location $Blockchain
try { & $npm exec -- hardhat run scripts/deploy.js --network localhost; if ($LASTEXITCODE -ne 0) { throw "Hardhat deploy failed." } } finally { Pop-Location }
$deploy = Get-Content (Join-Path $Blockchain "deployments\localhost.json") | ConvertFrom-Json
$updatedEnv = Get-Content $EnvFile | ForEach-Object { if ($_ -match '^\s*LANDCHAIN_CONTRACT_ADDRESS=') { "LANDCHAIN_CONTRACT_ADDRESS=$($deploy.address)" } else { $_ } }
if (-not ($updatedEnv -match '^LANDCHAIN_CONTRACT_ADDRESS=')) { $updatedEnv += "LANDCHAIN_CONTRACT_ADDRESS=$($deploy.address)" }
Set-Content -Path $EnvFile -Value $updatedEnv
Set-Location $Backend
& (Join-Path $Backend "venv\Scripts\python.exe") scripts\seed_dev.py
if ($LASTEXITCODE -ne 0) { throw "Seed failed. Development node PID: $($nodeProcess.Id)" }
Write-Host "DEVELOPMENT RESET COMPLETE. Hardhat PID: $($nodeProcess.Id). New contract: $($deploy.address)"
