param(
  [switch]$SkipE2E
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$web = Join-Path $root "web"
$report = Join-Path $root "web\tooling_bootstrap_report.json"

function Run-Step {
  param(
    [string]$Name,
    [string[]]$Command
  )
  $started = Get-Date
  Push-Location $web
  try {
    & $Command[0] @($Command[1..($Command.Count - 1)])
    $code = $LASTEXITCODE
  } finally {
    Pop-Location
  }
  @{
    name = $Name
    command = ($Command -join " ")
    exit_code = $code
    duration_seconds = [Math]::Round(((Get-Date) - $started).TotalSeconds, 3)
  }
}

$env:NODE_OPTIONS = (($env:NODE_OPTIONS, "--use-system-ca") -join " ").Trim()
$steps = New-Object System.Collections.Generic.List[object]
$status = "PASS"

try {
  $steps.Add((Run-Step "npm-ping" @("npm", "ping", "--fetch-timeout=15000", "--fetch-retries=0")))
  $install = if (Test-Path (Join-Path $web "package-lock.json")) { @("npm", "ci", "--maxsockets=1", "--fetch-retries=5") } else { @("npm", "install", "--maxsockets=1", "--fetch-retries=5") }
  $steps.Add((Run-Step "npm-install" $install))
  $steps.Add((Run-Step "npm-build" @("npm", "run", "build")))
  $steps.Add((Run-Step "npm-test" @("npm", "run", "test")))
  if (-not $SkipE2E) {
    $steps.Add((Run-Step "npm-e2e" @("npm", "run", "test:e2e")))
  }
} catch {
  $status = "FAIL_CLOSED"
  $steps.Add(@{
    name = "exception"
    exit_code = 2
    message = [string]$_.Exception.Message
  })
}

$payload = @{
  schema_id = "OC_CORE_DEMO_WEB_TOOLCHAIN_BOOTSTRAP_V003"
  status = $status
  node = (& node -v)
  npm = (& npm -v)
  node_options = $env:NODE_OPTIONS
  steps = $steps
  generated_at = (Get-Date).ToString("o")
}
$payload | ConvertTo-Json -Depth 8 | Set-Content -Path $report -Encoding UTF8
$payload | ConvertTo-Json -Depth 8
if ($status -ne "PASS") { exit 2 }
