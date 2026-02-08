param(
  [string]$DbName = "",
  [string]$DockerDbContainer = "hms-db",
  [string]$DbUser = "hms",
  [string]$DbPassword = "devpassword",
  [int]$HostPort = 5434
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function New-HmsRandomSecretHex([int]$ByteCount = 32) {
  $secretBytes = New-Object byte[] $ByteCount
  [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($secretBytes)
  return -join ($secretBytes | ForEach-Object { $_.ToString("x2") })
}

function Get-ComposeDbHostPort([int]$ContainerPort = 5432) {
  try {
    $raw = (docker compose port db $ContainerPort 2>$null) | Select-Object -First 1
    if (-not $raw) { return $null }
    # Formats like: "0.0.0.0:5434" or "::1:5434"
    $parts = $raw.Trim().Split(":")
    return [int]$parts[-1]
  } catch {
    return $null
  }
}

if (-not $DbName) {
  $DbName = "hms_perf_{0}" -f (Get-Date -Format "yyyyMMdd_HHmmss")
}

if ($DbName -notmatch "^hms_perf_[A-Za-z0-9_]+$") {
  throw "DbName must match ^hms_perf_[A-Za-z0-9_]+$. Got: '$DbName'"
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
  throw "docker is not available on PATH."
}
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
  throw "python is not available on PATH."
}

# Try to auto-detect the mapped Postgres port from compose; fall back to the default.
$detectedPort = Get-ComposeDbHostPort 5432
if ($detectedPort) {
  $HostPort = $detectedPort
}

$running = docker ps --format "{{.Names}}"
if (-not ($running -contains $DockerDbContainer)) {
  throw "Docker DB container '$DockerDbContainer' is not running. Start it with: docker compose up -d db"
}

Write-Host "[perf] Using DB container: $DockerDbContainer"
Write-Host "[perf] Target DB name: $DbName"
Write-Host "[perf] Host Postgres port: $HostPort"

# Create DB if it doesn't already exist.
$exists = docker exec -e "PGPASSWORD=$DbPassword" $DockerDbContainer `
  psql -U $DbUser -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname = '$DbName';"

if ("$exists".Trim() -ne "1") {
  Write-Host "[perf] Creating database '$DbName'..."
  docker exec -e "PGPASSWORD=$DbPassword" $DockerDbContainer `
    psql -U $DbUser -d postgres -v ON_ERROR_STOP=1 -c "CREATE DATABASE $DbName;"
} else {
  Write-Host "[perf] Database '$DbName' already exists; continuing."
}

$dbUrlHost = "postgresql+asyncpg://${DbUser}:${DbPassword}@localhost:$HostPort/$DbName"
$dbUrlDocker = "postgresql+asyncpg://${DbUser}:${DbPassword}@db:5432/$DbName"

# Run migrations + seed using local Python tooling.
$oldEnv = @{
  DATABASE_URL = $env:DATABASE_URL
  JWT_SECRET   = $env:JWT_SECRET
  CORS_ORIGINS = $env:CORS_ORIGINS
  SEED_DATA    = $env:SEED_DATA
}

$pushed = $false
try {
  $env:DATABASE_URL = $dbUrlHost
  if (-not $env:JWT_SECRET -or $env:JWT_SECRET.Trim().Length -lt 32) {
    $env:JWT_SECRET = New-HmsRandomSecretHex 32
  }
  # Ensure seed script creates demo accounts; app also seeds on startup when true.
  $env:SEED_DATA = "true"

  $repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\\..")
  $backendDir = Join-Path $repoRoot "backend"

  Push-Location $backendDir
  $pushed = $true
  Write-Host "[perf] Running migrations: alembic upgrade head"
  python -m alembic upgrade head
  if ($LASTEXITCODE -ne 0) { throw "alembic upgrade head failed" }

  Write-Host "[perf] Seeding: python -m app.scripts.seed"
  python -m app.scripts.seed
  if ($LASTEXITCODE -ne 0) { throw "seed script failed" }
} finally {
  if ($pushed) { Pop-Location -ErrorAction SilentlyContinue }
  foreach ($k in $oldEnv.Keys) {
    $v = $oldEnv[$k]
    if ($null -eq $v) {
      Remove-Item "Env:$k" -ErrorAction SilentlyContinue
    } else {
      Set-Item -Path "Env:$k" -Value $v
    }
  }
}

Write-Host ""
Write-Host "[perf] DONE. Disposable DB is ready."
Write-Host "[perf] DATABASE_URL (host):   $dbUrlHost"
Write-Host "[perf] DATABASE_URL (docker): $dbUrlDocker"
