#!/usr/bin/env pwsh
# Docker management script for LIFO project

param(
    [Parameter(Position = 0)]
    [ValidateSet('up', 'down', 'build', 'rebuild', 'logs', 'shell', 'clean', 'restart')]
    [string]$Command = 'up',
    
    [Parameter()]
    [switch]$Detach,
    
    [Parameter()]
    [switch]$Force
)

$projectRoot = Split-Path -Parent $PSScriptRoot
$composeFile = Join-Path $projectRoot "docker-compose.yml"

function Write-Status {
    param([string]$Message)
    Write-Host "📦 $Message" -ForegroundColor Cyan
}

function Test-DockerAvailable {
    try {
        docker info > $null 2>&1
        return $true
    }
    catch {
        Write-Host "❌ Docker is not running or not installed!" -ForegroundColor Red
        return $false
    }
}

function Invoke-DockerCompose {
    param([string[]]$Arguments)
    $cmd = "docker compose -f `"$composeFile`" $($Arguments -join ' ')"
    Write-Status "Running: $cmd"
    Invoke-Expression $cmd
}

# Ensure Docker is available
if (-not (Test-DockerAvailable)) {
    exit 1
}

# Process commands
switch ($Command) {
    'up' {
        Write-Status "Starting LIFO containers..."
        $args = @('up')
        if ($Detach) { $args += '-d' }
        Invoke-DockerCompose $args
    }
    'down' {
        Write-Status "Stopping LIFO containers..."
        Invoke-DockerCompose @('down')
    }
    'build' {
        Write-Status "Building LIFO containers..."
        Invoke-DockerCompose @('build', '--no-cache')
    }
    'rebuild' {
        Write-Status "Rebuilding LIFO containers..."
        Invoke-DockerCompose @('down', '--volumes')
        Invoke-DockerCompose @('build', '--no-cache')
        $args = @('up')
        if ($Detach) { $args += '-d' }
        Invoke-DockerCompose $args
    }
    'logs' {
        Write-Status "Showing LIFO container logs..."
        Invoke-DockerCompose @('logs', '--follow')
    }
    'shell' {
        Write-Status "Opening shell in LIFO app container..."
        Invoke-DockerCompose @('exec', 'app', '/bin/bash')
    }
    'clean' {
        Write-Status "Cleaning up LIFO containers and volumes..."
        if ($Force -or $PSCmdlet.ShouldContinue("This will remove all containers and volumes. Continue?", "Confirm cleanup")) {
            Invoke-DockerCompose @('down', '--volumes', '--remove-orphans')
            docker system prune -f
        }
    }
    'restart' {
        Write-Status "Restarting LIFO containers..."
        Invoke-DockerCompose @('restart')
    }
}