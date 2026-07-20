# Trackora Windows Build Script
# Compiles both the daemon and the GUI into a single package.

Write-Host "Checking for PyInstaller..." -ForegroundColor Blue
python -m pip install pyinstaller

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to install PyInstaller"
    exit 1
}

# Clean previous builds
Write-Host "Cleaning previous build artifacts..." -ForegroundColor Blue
Remove-Item -Path "build", "dist" -Recurse -ErrorAction SilentlyContinue

# Build the GUI dashboard
Write-Host "Building trackora-dashboard.exe..." -ForegroundColor Blue
# We bundle the assets folder containing fonts and logo matching internal package structure
python -m PyInstaller --noconfirm --windowed --name="trackora-dashboard" --add-data="trackora/assets;trackora/assets" trackora/gui/app.py

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to build trackora-dashboard.exe"
    exit 1
}

# Build the background daemon
Write-Host "Building trackora.exe (daemon)..." -ForegroundColor Blue
python -m PyInstaller --noconfirm --noconsole --name="trackora" trackora/__main__.py

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to build trackora.exe"
    exit 1
}

# Copy the daemon executable into the dashboard folder so they can run together
Write-Host "Consolidating executables..." -ForegroundColor Blue
Copy-Item -Path "dist/trackora/trackora.exe" -Destination "dist/trackora-dashboard/trackora.exe"

# Clean up separate daemon directory to keep package neat
Remove-Item -Path "dist/trackora" -Recurse -ErrorAction SilentlyContinue

Write-Host "Build complete! Standalone package is available in: dist/trackora-dashboard/" -ForegroundColor Green
