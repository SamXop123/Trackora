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

# Define modules to exclude to prevent bloating the executable with unrelated global packages
$excludes = @(
    "--exclude-module=torch",
    "--exclude-module=tensorflow",
    "--exclude-module=pandas",
    "--exclude-module=scipy",
    "--exclude-module=matplotlib",
    "--exclude-module=pygame",
    "--exclude-module=onnxruntime",
    "--exclude-module=keras",
    "--exclude-module=scikit-learn",
    "--exclude-module=sympy",
    "--exclude-module=lxml",
    "--exclude-module=numba",
    "--exclude-module=llvmlite",
    "--exclude-module=networkx",
    "--exclude-module=scikit-image",
    "--exclude-module=PIL",
    "--exclude-module=jinja2"
)

# Build the GUI dashboard
Write-Host "Building trackora-dashboard.exe..." -ForegroundColor Blue
# We bundle the assets folder and specify the app icon resource and hidden imports
python -m PyInstaller --noconfirm --windowed --name="trackora-dashboard" --icon="trackora/assets/trackora_logo.ico" --add-data="trackora/assets;trackora/assets" --collect-submodules="trackora" --hidden-import="windows" --hidden-import="windows.daemon" --hidden-import="windows.startup" --hidden-import="windows.tracker" $excludes trackora/gui/__main__.py

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to build trackora-dashboard.exe"
    exit 1
}

# Build the background daemon
Write-Host "Building trackora.exe (daemon)..." -ForegroundColor Blue
python -m PyInstaller --noconfirm --noconsole --name="trackora" --icon="trackora/assets/trackora_logo.ico" --collect-submodules="trackora" --hidden-import="windows" --hidden-import="windows.tracker" --hidden-import="windows.daemon" $excludes trackora/__main__.py

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
