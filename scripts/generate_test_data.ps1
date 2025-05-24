#!/usr/bin/env pwsh
# Script to generate test data and load it into PostgreSQL container

$ErrorActionPreference = "Stop"
$scriptPath = $PSScriptRoot
$projectRoot = Split-Path -Parent $scriptPath
$containerName = "my-postgres"

Write-Host "🚀 Starting test data generation and database loading process..." -ForegroundColor Cyan

# Function to run commands in the PostgreSQL container
function Invoke-DBCommand {
    param(
        [string]$Command,
        [string]$Database = "postgres"
    )
    try {
        $result = docker exec $containerName psql -U postgres -d $Database -c $Command
        if ($LASTEXITCODE -ne 0) {
            throw "Database command failed with exit code $LASTEXITCODE"
        }
        return $result
    }
    catch {
        Write-Host "❌ Error executing database command: $_" -ForegroundColor Red
        throw
    }
}

# Function to run SQL files in the PostgreSQL container
function Invoke-DBFile {
    param(
        [string]$FilePath,
        [string]$Database = "postgres"
    )
    try {
        if (-not (Test-Path $FilePath)) {
            throw "SQL file not found: $FilePath"
        }
        $containerPath = "/tmp/$(Split-Path -Leaf $FilePath)"
        docker cp $FilePath "${containerName}:$containerPath"
        if ($LASTEXITCODE -ne 0) { throw "Failed to copy file to container" }
        
        $result = docker exec $containerName psql -U postgres -d $Database -f $containerPath
        if ($LASTEXITCODE -ne 0) { throw "Failed to execute SQL file" }
        
        docker exec $containerName rm $containerPath
        return $result
    }
    catch {
        Write-Host "❌ Error processing SQL file: $_" -ForegroundColor Red
        throw
    }
}

# Function to wait for database to be ready
function Wait-ForDatabase {
    $retries = 30
    $ready = $false
    
    Write-Host "Waiting for database to be ready..." -ForegroundColor Yellow
    while (-not $ready -and $retries -gt 0) {
        try {
            $result = docker exec $containerName pg_isready -U postgres
            if ($LASTEXITCODE -eq 0) {
                $ready = $true
                Write-Host "Database is ready!" -ForegroundColor Green
                return
            }
        }
        catch {
            Write-Host "." -NoNewline
        }
        Start-Sleep -Seconds 1
        $retries--
    }
    
    throw "Database failed to become ready in time"
}

try {
    # Step 1: Check Docker is running
    try {
        docker ps | Out-Null
    }
    catch {
        throw "Docker is not running. Please start Docker Desktop first."
    }

    # Step 2: Ensure Docker services are running
    Write-Host "1️⃣ Checking Docker services..." -ForegroundColor Green
    
    # Check if containers need to be rebuilt
    $rebuild = $false
    if (-not (Test-Path (Join-Path $projectRoot "database\sample_data.sql"))) {
        $rebuild = $true
    }
    
    # Stop existing containers if rebuilding
    if ($rebuild) {
        Write-Host "Stopping existing containers..." -ForegroundColor Yellow
        docker compose down --volumes
    }
    
    # Start containers
    $dbRunning = docker ps --filter "name=$containerName" --format '{{.Names}}'
    if (-not $dbRunning -or $rebuild) {
        Write-Host "Starting Docker services..."
        docker compose up -d --build
        Wait-ForDatabase
    }

    # Step 3: Install Python dependencies locally
    Write-Host "2️⃣ Installing Python dependencies..." -ForegroundColor Green
    Push-Location $projectRoot
    try {
        # Check if UV is installed
        if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
            Write-Host "Installing UV package manager..." -ForegroundColor Yellow
            Invoke-WebRequest -Uri "https://astral.sh/uv/install.ps1" -OutFile "install-uv.ps1"
            .\install-uv.ps1
            Remove-Item "install-uv.ps1"
            if (-not (Get-Command uv -ErrorAction SilentlyContinue)) { throw "Failed to install UV" }
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "User") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "Machine")
        }
        
        # Install project dependencies
        Write-Host "Installing project dependencies..." -ForegroundColor Yellow
        uv pip install -e .
        if ($LASTEXITCODE -ne 0) { throw "Failed to install project dependencies" }
    }
    finally {
        Pop-Location
    }
    
    # Step 4: Generate sample data
    Write-Host "3️⃣ Generating sample data..." -ForegroundColor Green
    Push-Location $projectRoot
    try {
        python -m app.main
        
        # Verify sample data file was created
        $sampleDataScript = Join-Path $projectRoot "database\sample_data.sql"
        if (-not (Test-Path $sampleDataScript)) {
            throw "Sample data generation failed: $sampleDataScript not created"
        }
    }
    finally {
        Pop-Location
    }

    # Step 5: Load sample data
    Write-Host "4️⃣ Loading sample data into database..." -ForegroundColor Green
    $sampleDataScript = Join-Path $projectRoot "database\sample_data.sql"
    Invoke-DBFile -FilePath $sampleDataScript -Database "lifo"
    Write-Host "✅ Sample data loaded successfully!" -ForegroundColor Green
    
    # Step 6: Verify data
    Write-Host "`n📊 Verifying data counts:" -ForegroundColor Cyan
    $verificationQueries = @(
        "SELECT 'Stores' as table_name, COUNT(*) as count FROM stores;",
        "SELECT 'Products' as table_name, COUNT(*) as count FROM products;",
        "SELECT 'Suppliers' as table_name, COUNT(*) as count FROM suppliers;",
        "SELECT 'Batches' as table_name, COUNT(*) as count FROM product_batches;",
        "SELECT 'Movements' as table_name, COUNT(*) as count FROM inventory_movements;",
        "SELECT 'Scores' as table_name, COUNT(*) as count FROM batch_scores;"
    )

    foreach ($query in $verificationQueries) {
        Invoke-DBCommand -Command $query -Database "lifo"
    }
    
    Write-Host "`n✅ Data generation and verification complete!" -ForegroundColor Green
}
catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
    Write-Host "Stack Trace: $($_.ScriptStackTrace)" -ForegroundColor Red
    exit 1
}
