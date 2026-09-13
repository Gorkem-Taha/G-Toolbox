#!/usr/bin/env bash
# ==============================================================================
# G-Toolbox — Linux AppImage Build Script
# Creates a standalone, portable G-Toolbox-x86_64.AppImage for any Linux distro.
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
BUILD_DIR="${ROOT_DIR}/build_appimage"
APP_DIR="${BUILD_DIR}/AppDir"
OUTPUT_DIR="${ROOT_DIR}/dist"
ARCH="$(uname -m)"

echo "=========================================================="
echo " 🚀 Building G-Toolbox AppImage for Linux (${ARCH})"
echo "=========================================================="

mkdir -p "${BUILD_DIR}" "${OUTPUT_DIR}"
rm -rf "${APP_DIR}"
mkdir -p "${APP_DIR}/usr/bin"
mkdir -p "${APP_DIR}/usr/lib"
mkdir -p "${APP_DIR}/usr/share/icons/hicolor/256x256/apps"
mkdir -p "${APP_DIR}/app"

# 1. Copy Application Source Files
echo "[1/6] Copying application files..."
cp -r "${ROOT_DIR}/main.py" "${APP_DIR}/app/"
cp -r "${ROOT_DIR}/desktop_app.py" "${APP_DIR}/app/"
cp -r "${ROOT_DIR}/templates" "${APP_DIR}/app/"
cp -r "${ROOT_DIR}/static" "${APP_DIR}/app/"
if [ -d "${ROOT_DIR}/utils" ]; then
    cp -r "${ROOT_DIR}/utils" "${APP_DIR}/app/"
fi
if [ -f "${ROOT_DIR}/requirements.txt" ]; then
    cp "${ROOT_DIR}/requirements.txt" "${APP_DIR}/app/"
fi

# 2. Setup Desktop Entry & Icons
echo "[2/6] Configuring desktop integration..."
cat << 'EOF' > "${APP_DIR}/g-toolbox.desktop"
[Desktop Entry]
Name=G-Toolbox
Comment=All-in-One Media & AI Studio
Exec=AppRun %U
Icon=g-toolbox
Type=Application
Categories=AudioVideo;Audio;Video;Graphics;Utility;
Terminal=false
StartupWMClass=G-Toolbox
EOF

cp "${APP_DIR}/g-toolbox.desktop" "${APP_DIR}/usr/share/applications/g-toolbox.desktop" 2>/dev/null || true

# Prepare application icon
if [ -f "${ROOT_DIR}/static/icon.png" ]; then
    cp "${ROOT_DIR}/static/icon.png" "${APP_DIR}/g-toolbox.png"
    cp "${ROOT_DIR}/static/icon.png" "${APP_DIR}/usr/share/icons/hicolor/256x256/apps/g-toolbox.png"
    cp "${ROOT_DIR}/static/icon.png" "${APP_DIR}/.DirIcon"
elif [ -f "${ROOT_DIR}/static/favicon.ico" ]; then
    cp "${ROOT_DIR}/static/favicon.ico" "${APP_DIR}/g-toolbox.ico"
fi

# 3. Create Custom AppRun Entrypoint
echo "[3/6] Generating AppRun launcher..."
cat << 'EOF' > "${APP_DIR}/AppRun"
#!/usr/bin/env bash
HERE="$(dirname "$(readlink -f "${0}")")"
export APPDIR="${HERE}"
export PATH="${HERE}/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/lib:${LD_LIBRARY_PATH}"
export PYTHONPATH="${HERE}/app:${HERE}/usr/lib/python3/dist-packages:${PYTHONPATH}"

cd "${HERE}/app"

# Check if desktop mode can be run or fallback to default browser
if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
elif [ -f "${HERE}/usr/bin/python3" ]; then
    PYTHON_BIN="${HERE}/usr/bin/python3"
else
    echo "Python 3 is required to run G-Toolbox."
    exit 1
fi

exec "${PYTHON_BIN}" "${HERE}/app/desktop_app.py" "$@"
EOF

chmod +x "${APP_DIR}/AppRun"

# 4. Download appimagetool if not available
echo "[4/6] Checking appimagetool..."
APPIMAGETOOL="${BUILD_DIR}/appimagetool"
if [ ! -f "${APPIMAGETOOL}" ]; then
    echo "Downloading appimagetool-x86_64.AppImage..."
    curl -sL "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage" -o "${APPIMAGETOOL}"
    chmod +x "${APPIMAGETOOL}"
fi

# 5. Build AppImage
echo "[5/6] Packaging AppImage..."
export ARCH="x86_64"
OUTPUT_NAME="G-Toolbox-${ARCH}.AppImage"

# Use --appimage-extract-and-run if FUSE is not available in Docker / CI
if [ -n "${GITHUB_ACTIONS}" ] || [ ! -c /dev/fuse ]; then
    "${APPIMAGETOOL}" --appimage-extract-and-run "${APP_DIR}" "${OUTPUT_DIR}/${OUTPUT_NAME}"
else
    "${APPIMAGETOOL}" "${APP_DIR}" "${OUTPUT_DIR}/${OUTPUT_NAME}"
fi

chmod +x "${OUTPUT_DIR}/${OUTPUT_NAME}"

echo "=========================================================="
echo " ✅ Successfully created: ${OUTPUT_DIR}/${OUTPUT_NAME}"
echo " To run on Linux: chmod +x ${OUTPUT_NAME} && ./${OUTPUT_NAME}"
echo "=========================================================="
