#!/usr/bin/env bash
#
# Trackora RPM Build Helper Script
# This script prepares the RPM build environment and generates the RPM package.
#

set -euo pipefail

# 1. Detect project version from pyproject.toml
if [ ! -f "pyproject.toml" ]; then
    echo "Error: pyproject.toml not found in the current directory." >&2
    exit 1
fi

VERSION=$(python3 -c "
import re
content = open('pyproject.toml').read()
match = re.search(r'version\s*=\s*\"([^\"]+)\"', content)
if match:
    print(match.group(1))
else:
    raise ValueError('Could not find version in pyproject.toml')
")

echo "Detected version: ${VERSION}"

# 2. Sync version to trackora.spec
if [ -f "trackora.spec" ]; then
    echo "Syncing version ${VERSION} to trackora.spec..."
    sed -i "s/^Version:.*/Version:        ${VERSION}/" trackora.spec
else
    echo "Error: trackora.spec not found." >&2
    exit 1
fi

# 3. Create clean RPM build environment
echo "Setting up rpmbuild directories..."
rm -rf rpmbuild
mkdir -p rpmbuild/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

# Copy SPEC file to SPECS directory
cp trackora.spec rpmbuild/SPECS/

# 4. Create source tarball
echo "Creating source tarball: rpmbuild/SOURCES/trackora-${VERSION}.tar.gz..."
TEMP_DIR=$(mktemp -d)
trap 'rm -rf "${TEMP_DIR}"' EXIT

mkdir -p "${TEMP_DIR}/trackora-${VERSION}"

# Copy all source files cleanly excluding build artifacts
rsync -a \
    --exclude="rpmbuild" \
    --exclude="dist" \
    --exclude=".git" \
    --exclude="*demo.db*" \
    --exclude="*.pyc" \
    --exclude="__pycache__" \
    ./ "${TEMP_DIR}/trackora-${VERSION}/"

tar -czf "rpmbuild/SOURCES/trackora-${VERSION}.tar.gz" -C "${TEMP_DIR}" "trackora-${VERSION}"

echo "Source tarball created successfully."

# 5. Build the RPM package
if [[ "${1:-}" == "--setup-only" ]]; then
    echo "Setup complete. Source tarball and SPEC file are in place."
    echo "To build the RPM, run: rpmbuild --define \"_topdir $(pwd)/rpmbuild\" -ba trackora.spec"
    exit 0
fi

echo "Building RPM package..."
rpmbuild --define "_topdir $(pwd)/rpmbuild" -ba trackora.spec

# Normalize the version name for output files (e.g. 1.0.0rc1 -> 1.0.0-rc1)
FILE_VERSION=$(echo "${VERSION}" | sed 's/rc/-rc/')

mkdir -p dist

# 6. Copy and rename the built RPM
RPM_FILE=$(find rpmbuild/RPMS -name "*.rpm" | head -n 1)
if [ -n "${RPM_FILE}" ]; then
    cp "${RPM_FILE}" "dist/trackora-${FILE_VERSION}.rpm"
else
    echo "Error: Built RPM package not found." >&2
    exit 1
fi

# 7. Create the release source tarball
echo "Creating release source archive: dist/trackora-${FILE_VERSION}.tar.gz..."
RELEASE_TEMP_DIR=$(mktemp -d)
mkdir -p "${RELEASE_TEMP_DIR}/Trackora"

# Copy all source files cleanly, excluding build artifacts
rsync -a \
    --exclude="rpmbuild" \
    --exclude="dist" \
    --exclude=".git" \
    --exclude="*demo.db*" \
    --exclude="*.pyc" \
    --exclude="__pycache__" \
    --exclude=".pytest_cache" \
    --exclude=".venv" \
    ./ "${RELEASE_TEMP_DIR}/Trackora/"

tar -czf "dist/trackora-${FILE_VERSION}.tar.gz" -C "${RELEASE_TEMP_DIR}" "Trackora"
rm -rf "${RELEASE_TEMP_DIR}"

echo "--------------------------------------------------------"
echo "Build Completed Successfully!"
echo "Release artifacts generated in dist/:"
ls -lh dist/
echo "--------------------------------------------------------"
