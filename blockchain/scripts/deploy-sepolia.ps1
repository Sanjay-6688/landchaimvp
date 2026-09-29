$ErrorActionPreference = "Stop"

$blockchainDirectory = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$projectDirectory = (Resolve-Path (Join-Path $blockchainDirectory "..")).Path
$backendEnvPath = Join-Path $projectDirectory "backend\.env"
$walletPath = Join-Path $blockchainDirectory ".local-sepolia-wallet.json"

if (!(Test-Path -LiteralPath $backendEnvPath)) { throw "Create backend\.env first." }
if (!(Test-Path -LiteralPath $walletPath)) { throw "Create the demo wallet first with npm run wallet:sepolia-demo." }

$rpcLine = Get-Content -LiteralPath $backendEnvPath | Where-Object { $_ -match '^\s*SEPOLIA_RPC_URL\s*=' } | Select-Object -First 1
$rpcUrl = if ($rpcLine) { ($rpcLine -split '=', 2)[1].Trim().Trim('"').Trim("'") } else { "" }
if ([string]::IsNullOrWhiteSpace($rpcUrl)) { throw "Set SEPOLIA_RPC_URL in backend\.env using your Sepolia RPC provider endpoint." }

$wallet = Get-Content -LiteralPath $walletPath -Raw | ConvertFrom-Json
if ($wallet.address -notmatch '^0x[a-fA-F0-9]{40}$' -or $wallet.privateKey -notmatch '^0x[a-fA-F0-9]{64}$') {
    throw "The local demo wallet file is invalid. Do not print or paste its private key."
}

$previousRpc = $env:SEPOLIA_RPC_URL
$previousKey = $env:BLOCKCHAIN_PRIVATE_KEY
try {
    $env:SEPOLIA_RPC_URL = $rpcUrl
    $env:BLOCKCHAIN_PRIVATE_KEY = $wallet.privateKey
    Push-Location $blockchainDirectory
    npm run deploy:sepolia
    if ($LASTEXITCODE -ne 0) { throw "Sepolia deployment failed. Check the RPC URL and ensure the demo wallet has Sepolia test ETH." }
}
finally {
    Pop-Location -ErrorAction SilentlyContinue
    if ($null -eq $previousRpc) { Remove-Item Env:\SEPOLIA_RPC_URL -ErrorAction SilentlyContinue } else { $env:SEPOLIA_RPC_URL = $previousRpc }
    if ($null -eq $previousKey) { Remove-Item Env:\BLOCKCHAIN_PRIVATE_KEY -ErrorAction SilentlyContinue } else { $env:BLOCKCHAIN_PRIVATE_KEY = $previousKey }
    $rpcUrl = $null
    $wallet = $null
}
