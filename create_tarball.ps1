$tempDir = "scratch/trackora-2.1.0-archive"
if (Test-Path $tempDir) { Remove-Item -Path $tempDir -Recurse -Force }
New-Item -ItemType Directory -Path "$tempDir/Trackora" -Force | Out-Null

$filesToCopy = @(
    "trackora",
    "windows",
    "shell-extension",
    "systemd",
    "install.sh",
    "uninstall.sh",
    "pyproject.toml",
    "README.md",
    "LICENSE",
    "CONTRIBUTING.md"
)

foreach ($item in $filesToCopy) {
    if (Test-Path $item) {
        Copy-Item -Path $item -Destination "$tempDir/Trackora/" -Recurse -Force
    }
}

if (-not (Test-Path "dist")) { New-Item -ItemType Directory -Path "dist" | Out-Null }
if (-not (Test-Path "landing/public")) { New-Item -ItemType Directory -Path "landing/public" | Out-Null }

tar -czf "dist/trackora-2.1.0.tar.gz" -C $tempDir Trackora
Copy-Item -Path "dist/trackora-2.1.0.tar.gz" -Destination "landing/public/trackora-2.1.0.tar.gz" -Force
Remove-Item -Path $tempDir -Recurse -Force
Write-Host "Successfully generated trackora-2.1.0.tar.gz in dist/ and landing/public/" -ForegroundColor Green
