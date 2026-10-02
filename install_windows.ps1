param([int]$Port = 5000)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$repoZipUrl = "https://github.com/aimanaltoubi/situational-room/archive/refs/heads/main.zip"
$installRoot = Join-Path $env:LOCALAPPDATA "SituationalRoom"
$venvPath = Join-Path $installRoot ".venv"
$venvPython = Join-Path $venvPath "Scripts\python.exe"
$envFile = Join-Path $installRoot ".env"
$firstInstall = !(Test-Path (Join-Path $installRoot "app.py"))

function Refresh-ProcessPath {
    $machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$env:Path;$machinePath;$userPath"
}

function Install-WingetPackage([string]$PackageId) {
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if (!$winget) {
        throw "winget is unavailable. Install Python 3.11 and a Java 17 runtime, then run this command again."
    }

    & $winget.Source install --id $PackageId --exact --silent `
        --accept-package-agreements --accept-source-agreements | Out-Host
    if ($LASTEXITCODE -ne 0) {
        throw "winget could not install $PackageId (exit code $LASTEXITCODE)."
    }
    Refresh-ProcessPath
}

function Get-Python311 {
    if (!(Get-Command py -ErrorAction SilentlyContinue)) {
        Install-WingetPackage "Python.Python.3.11"
    }

    $python = & py -3.11 -c "import sys; print(sys.executable)"
    if ($LASTEXITCODE -ne 0 -or !$python) {
        Install-WingetPackage "Python.Python.3.11"
        $python = & py -3.11 -c "import sys; print(sys.executable)"
    }
    if ($LASTEXITCODE -ne 0 -or !$python) {
        throw "Python 3.11 was not found. Install it and rerun this command."
    }
    return $python.Trim()
}

function Test-RequiredApiKeys {
    $requiredKeys = @("GEMINI_API_KEY", "CESIUM_TOKEN", "ADSBX_KEY", "DATALASTIC_KEY")
    $contents = Get-Content -LiteralPath $envFile
    $missingKeys = @()
    foreach ($key in $requiredKeys) {
        if (!($contents | Where-Object { $_ -match "^\s*$key\s*=\s*\S+" })) {
            $missingKeys += $key
        }
    }
    return $missingKeys
}

if ($firstInstall) {
    Write-Host "Downloading Situational Room..."
    $staging = Join-Path $env:TEMP ("SituationalRoom-" + [guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Path $staging -Force | Out-Null
    try {
        $zipPath = Join-Path $staging "source.zip"
        $extractPath = Join-Path $staging "source"
        Invoke-WebRequest -Uri $repoZipUrl -OutFile $zipPath
        Expand-Archive -LiteralPath $zipPath -DestinationPath $extractPath -Force
        $sourceRoot = Get-ChildItem -LiteralPath $extractPath -Directory | Select-Object -First 1
        if (!$sourceRoot) {
            throw "The downloaded archive did not contain the application files."
        }
        New-Item -ItemType Directory -Path $installRoot -Force | Out-Null
        Copy-Item -Path (Join-Path $sourceRoot.FullName "*") `
            -Destination $installRoot -Recurse -Force
    }
    finally {
        Remove-Item -LiteralPath $staging -Recurse -Force -ErrorAction SilentlyContinue
    }
}

$pythonExe = Get-Python311
if (!(Get-Command java -ErrorAction SilentlyContinue)) {
    Install-WingetPackage "EclipseAdoptium.Temurin.17.JRE"
}
if (!(Get-Command java -ErrorAction SilentlyContinue)) {
    throw "Java was not found after installation. Install a Java 17 runtime and rerun this command."
}

if (!(Test-Path $venvPython)) {
    Write-Host "Creating the application environment and installing dependencies..."
    & $pythonExe -m venv $venvPath
    if ($LASTEXITCODE -ne 0) { throw "Could not create the Python environment." }
    & $venvPython -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) { throw "Could not upgrade pip." }
    & $venvPython -m pip install -r (Join-Path $installRoot "requirements.txt")
    if ($LASTEXITCODE -ne 0) { throw "Could not install application dependencies." }
}

if (!(Test-Path $envFile)) {
    Copy-Item (Join-Path $installRoot ".env.example") $envFile
}

$missingKeys = Test-RequiredApiKeys
if ($missingKeys.Count -gt 0) {
    Write-Host "Add your API keys in Notepad. The app needs: $($missingKeys -join ', ')"
    Start-Process notepad.exe -ArgumentList $envFile -Wait
    $missingKeys = Test-RequiredApiKeys
    if ($missingKeys.Count -gt 0) {
        throw "Missing API keys: $($missingKeys -join ', '). Edit $envFile and rerun this command."
    }
}

$statusUrl = "http://127.0.0.1:$Port/status"
try {
    $status = Invoke-WebRequest -Uri $statusUrl -UseBasicParsing -TimeoutSec 2
    if ($status.StatusCode -eq 200) {
        Start-Process "http://localhost:$Port"
        Write-Host "Situational Room is already running at http://localhost:$Port"
        exit 0
    }
}
catch { }

if ($firstInstall -or !(Test-Path (Join-Path $installRoot "output\ifs_globe.html"))) {
    Write-Host "Building the dashboard for the first run. This can take several minutes..."
    & $venvPython (Join-Path $installRoot "run_pipeline.py") --skip-scrape
    if ($LASTEXITCODE -ne 0) { throw "The data pipeline exited with code $LASTEXITCODE." }
    if (!(Test-Path (Join-Path $installRoot "output\ifs_globe.html"))) {
        throw "The pipeline did not create the dashboard. Check API keys, data files, and the pipeline output, then rerun this command."
    }
    $weeklyReport = Get-ChildItem -LiteralPath (Join-Path $installRoot "output") `
        -Filter "weekly_prediction_*.html" -File | Select-Object -First 1
    if (!$weeklyReport) {
        throw "The weekly forecast was not generated. Check the H2O/Java setup and pipeline output, then rerun this command."
    }
}

$logsPath = Join-Path $installRoot "logs"
New-Item -ItemType Directory -Path $logsPath -Force | Out-Null
$server = Start-Process -FilePath $venvPython `
    -ArgumentList @("app.py", "--port", "$Port") `
    -WorkingDirectory $installRoot -PassThru `
    -RedirectStandardOutput (Join-Path $logsPath "windows-app.log") `
    -RedirectStandardError (Join-Path $logsPath "windows-app-error.log")

$ready = $false
for ($attempt = 0; $attempt -lt 45; $attempt++) {
    if ($server.HasExited) { break }
    try {
        $status = Invoke-WebRequest -Uri $statusUrl -UseBasicParsing -TimeoutSec 2
        if ($status.StatusCode -eq 200) {
            $ready = $true
            break
        }
    }
    catch { }
    Start-Sleep -Seconds 1
}

if (!$ready) {
    if (!$server.HasExited) { Stop-Process -Id $server.Id -Force }
    throw "The web server did not start. Review $logsPath for details."
}

Start-Process "http://localhost:$Port"
Write-Host "Situational Room is running at http://localhost:$Port"
Write-Host "Server process ID: $($server.Id)"
Write-Host "Stop it from CMD with: taskkill /PID $($server.Id) /T /F"
Write-Host "Logs: $logsPath"