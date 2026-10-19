[CmdletBinding()]
param(
    [switch]$NoBrowser,
    [int]$ReadyTimeoutSeconds = 120
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$RuntimeLogDirectory = Join-Path $ProjectRoot "development\runtime_logs"
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$GardenApiScript = Join-Path $ProjectRoot "scripts\run_garden_preview_api.py"
$FrontendDirectory = Join-Path $ProjectRoot "frontend"
$AceStepHome = if ($env:MUSEGARDEN_ACESTEP_HOME) {
    $env:MUSEGARDEN_ACESTEP_HOME
} else {
    "D:\MuseGarden-ace-step-poc\ACE-Step 1.5"
}
$AceStepScript = Join-Path $AceStepHome "start_musegarden_api.bat"

function Test-LocalPort {
    param([int]$Port)

    $client = [System.Net.Sockets.TcpClient]::new()
    try {
        $connection = $client.ConnectAsync("127.0.0.1", $Port)
        if (-not $connection.Wait(800)) { return $false }
        return $client.Connected
    } catch {
        return $false
    } finally {
        $client.Dispose()
    }
}

function Wait-ForLocalPort {
    param(
        [string]$Name,
        [int]$Port
    )

    $deadline = (Get-Date).AddSeconds($ReadyTimeoutSeconds)
    while (-not (Test-LocalPort -Port $Port)) {
        if ((Get-Date) -ge $deadline) {
            throw "$Name did not become ready within $ReadyTimeoutSeconds seconds (127.0.0.1:$Port). Check $RuntimeLogDirectory."
        }
        Start-Sleep -Milliseconds 500
    }
    Write-Host "[READY] $Name (127.0.0.1:$Port)"
}

function Start-LocalProcess {
    param(
        [string]$Name,
        [string]$FilePath,
        [string[]]$Arguments,
        [string]$WorkingDirectory
    )

    $stdout = Join-Path $RuntimeLogDirectory "$Name.stdout.log"
    $stderr = Join-Path $RuntimeLogDirectory "$Name.stderr.log"
    Start-Process -FilePath $FilePath -ArgumentList $Arguments -WorkingDirectory $WorkingDirectory `
        -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr | Out-Null
    Write-Host "[STARTED] $Name"
}

if (-not (Test-Path -LiteralPath $Python)) {
    throw "Project Python environment was not found: $Python"
}
if (-not (Test-Path -LiteralPath $AceStepScript)) {
    throw "ACE-Step start script was not found: $AceStepScript. Set MUSEGARDEN_ACESTEP_HOME to the ACE-Step directory."
}

New-Item -ItemType Directory -Force -Path $RuntimeLogDirectory | Out-Null

if (-not (Test-LocalPort -Port 11434)) {
    $ollama = Get-Command ollama -ErrorAction SilentlyContinue
    if ($null -eq $ollama) {
        throw "Ollama is not on PATH and is not running at 127.0.0.1:11434."
    }
    Start-LocalProcess -Name "ollama" -FilePath $ollama.Source -Arguments @("serve") -WorkingDirectory $ProjectRoot
}
Wait-ForLocalPort -Name "Ollama" -Port 11434

if (-not (Test-LocalPort -Port 8001)) {
    Start-LocalProcess -Name "ace-step" -FilePath "cmd.exe" -Arguments @("/c", "`"$AceStepScript`"") -WorkingDirectory $AceStepHome
}
Wait-ForLocalPort -Name "ACE-Step" -Port 8001

if (-not (Test-LocalPort -Port 8000)) {
    Start-LocalProcess -Name "garden-api" -FilePath $Python -Arguments @($GardenApiScript) -WorkingDirectory $ProjectRoot
}
Wait-ForLocalPort -Name "Garden API" -Port 8000

if (-not (Test-LocalPort -Port 5182)) {
    $npm = Get-Command npm.cmd -ErrorAction SilentlyContinue
    if ($null -eq $npm) { $npm = Get-Command npm -ErrorAction SilentlyContinue }
    if ($null -eq $npm) {
        throw "npm was not found, so the frontend cannot start."
    }
    Start-LocalProcess -Name "frontend" -FilePath $npm.Source -Arguments @("run", "dev", "--", "--port", "5182") -WorkingDirectory $FrontendDirectory
}
Wait-ForLocalPort -Name "MuseGarden Frontend" -Port 5182

$Url = "http://127.0.0.1:5182/"
Write-Host "MuseGarden is ready: $Url"
if (-not $NoBrowser) {
    Start-Process $Url
}
