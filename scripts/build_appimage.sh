#!/usr/bin/env bash
# ==============================================================================
# G-Toolbox — Linux AppImage build
#
# Produces a self-contained G-Toolbox-x86_64.AppImage that bundles:
#   • a relocatable CPython 3.11 (python-build-standalone, SHA-256 pinned)
#   • the core Python dependencies, hash-locked (requirements-core.lock)
#   • a static ffmpeg/ffprobe (BtbN, verified against the release checksums)
# AI engines (torch, rembg, …) are installed on demand from the app into
# ~/.local/share/g-toolbox/site-packages, since the AppImage itself is read-only.
#
# Usage: scripts/build_appimage.sh [--no-ffmpeg]
# Output: dist/G-Toolbox-x86_64.AppImage
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
BUILD_DIR="${ROOT_DIR}/build_appimage"
CACHE_DIR="${BUILD_DIR}/cache"
APP_DIR="${BUILD_DIR}/AppDir"
OUTPUT_DIR="${ROOT_DIR}/dist"
WITH_FFMPEG=1
[[ "${1:-}" == "--no-ffmpeg" ]] && WITH_FFMPEG=0

# ── Pinned inputs ─────────────────────────────────────────────────────────────
PY_TAG="20261026"
PY_ASSET="cpython-3.11.18+${PY_TAG}-x86_64-unknown-linux-gnu-install_only.tar.gz"
PY_SHA256="a87ee63646c8f8438b7af3954b2135ed2af91d033c631f12a8f20af903046d06"
APPIMAGETOOL_VERSION="1.9.1"
APPIMAGETOOL_SHA256="ed4ce84f0d9caff66f50bcca6ff6f35aae54ce8135408b3fa33abfc3cb384eb0"
RUNTIME_TAG="20251108"   # AppImage type2 runtime embedded in the output
RUNTIME_SHA256="2fca8b443c92510f1483a883f60061ad09b46b978b2631c807cd873a47ec260d"
# BtbN only keeps rolling "latest" builds of each release branch, so the hash is
# checked against that release's published checksums.sha256 instead of pinned.
GLIBC_FLOOR="2.28"   # newest glibc any bundled ELF file may require
FFMPEG_ASSET="ffmpeg-n8.1-latest-linux64-gpl-8.1.tar.xz"
FFMPEG_BASE="https://github.com/BtbN/FFmpeg-Builds/releases/download/latest"

fetch() {  # fetch <url> <dest> [sha256]
  local url="$1" dest="$2" sha="${3:-}"
  if [[ ! -f "$dest" ]]; then
    echo "    ↓ $url"
    curl -fsSL --retry 3 --proto '=https' --tlsv1.2 -o "$dest.part" "$url"
    mv "$dest.part" "$dest"
  fi
  if [[ -n "$sha" ]]; then
    echo "$sha  $dest" | sha256sum -c --quiet - || { rm -f "$dest"; echo "SHA-256 mismatch: $dest" >&2; exit 1; }
  fi
}

echo "=========================================================="
echo " 🚀 Building G-Toolbox AppImage (x86_64)"
echo "=========================================================="
mkdir -p "$CACHE_DIR" "$OUTPUT_DIR"
rm -rf "$APP_DIR"
mkdir -p "$APP_DIR/usr/bin" "$APP_DIR/usr/share/applications" \
         "$APP_DIR/usr/share/icons/hicolor/64x64/apps" "$APP_DIR/app"

echo "[1/6] Bundled Python ${PY_ASSET%%-x86_64*}"
fetch "https://github.com/astral-sh/python-build-standalone/releases/download/${PY_TAG}/${PY_ASSET}" \
      "$CACHE_DIR/$PY_ASSET" "$PY_SHA256"
tar -xzf "$CACHE_DIR/$PY_ASSET" -C "$APP_DIR/usr"   # → usr/python
PY="$APP_DIR/usr/python/bin/python3"

echo "[2/6] Core Python dependencies"
# Wheels for glibc 2.28 (RHEL 8, Debian 10, Ubuntu 20.04) whatever the build host
# runs: pip would otherwise pick the newest manylinux tag the host supports.
SITE_PACKAGES="$("$PY" -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')"
# pip does not widen an explicit --platform to older manylinux tags: list them all
PLATFORMS=()
for minor in $(seq "${GLIBC_FLOOR#2.}" -1 5); do PLATFORMS+=(--platform "manylinux_2_${minor}_x86_64"); done
PLATFORMS+=(--platform manylinux2014_x86_64 --platform manylinux2010_x86_64 --platform manylinux1_x86_64)
"$PY" -m pip install --quiet --no-warn-script-location --disable-pip-version-check \
      --require-hashes --only-binary=:all: \
      "${PLATFORMS[@]}" --implementation cp --python-version 3.11 \
      --target "$SITE_PACKAGES" -r "$ROOT_DIR/requirements-core.lock"
# Byte-code is generated at build time; the AppImage is read-only at runtime.
"$PY" -m compileall -q "$APP_DIR/usr/python/lib" >/dev/null || true

if [[ "$WITH_FFMPEG" == 1 ]]; then
  echo "[3/6] Static ffmpeg (${FFMPEG_ASSET})"
  rm -f "$CACHE_DIR/ffmpeg-checksums.sha256"   # rolling build: never reuse an old checksum list
  fetch "${FFMPEG_BASE}/checksums.sha256" "$CACHE_DIR/ffmpeg-checksums.sha256"
  FF_SHA="$(awk -v f="$FFMPEG_ASSET" '$2==f || $2=="*"f {print $1}' "$CACHE_DIR/ffmpeg-checksums.sha256")"
  [[ -n "$FF_SHA" ]] || { echo "No checksum published for $FFMPEG_ASSET" >&2; exit 1; }
  rm -f "$CACHE_DIR/$FFMPEG_ASSET"   # rolling build: always fetch the one matching today's checksums
  fetch "${FFMPEG_BASE}/${FFMPEG_ASSET}" "$CACHE_DIR/$FFMPEG_ASSET" "$FF_SHA"
  tar -xJf "$CACHE_DIR/$FFMPEG_ASSET" -C "$BUILD_DIR"
  FF_DIR="$BUILD_DIR/${FFMPEG_ASSET%.tar.xz}"
  install -m 755 "$FF_DIR/bin/ffmpeg" "$FF_DIR/bin/ffprobe" "$APP_DIR/usr/bin/"
  mkdir -p "$APP_DIR/usr/share/licenses/ffmpeg"
  cp "$FF_DIR/LICENSE.txt" "$APP_DIR/usr/share/licenses/ffmpeg/" 2>/dev/null || true
  cat > "$APP_DIR/usr/share/licenses/ffmpeg/README" <<EOF
This AppImage includes an unmodified static FFmpeg build (GPL) from
https://github.com/BtbN/FFmpeg-Builds (${FFMPEG_ASSET}).
Corresponding source code: https://github.com/BtbN/FFmpeg-Builds and https://ffmpeg.org
EOF
  rm -rf "$FF_DIR"
else
  echo "[3/6] Skipping ffmpeg (system ffmpeg will be used if installed)"
fi

# Same measure as AppImageHub's code/check-libc.sh: the newest GLIBC_ version of
# any undefined symbol in a dynamic ELF file must not exceed the floor.
NEWEST_GLIBC="$(find "$APP_DIR" -type f -print0 | while IFS= read -r -d '' f; do
  [ "$(od -An -tx1 -N4 "$f" 2>/dev/null)" == " 7f 45 4c 46" ] || continue
  objdump -T "$f" 2>/dev/null | grep '\*UND\*' | grep -oE 'GLIBC_[0-9]+(\.[0-9]+)+' | sed "s|^|$f |"
done | sort -k2,2V | tail -n 1)"
if [ -n "$NEWEST_GLIBC" ]; then
  NEWEST="${NEWEST_GLIBC##*GLIBC_}"
  if [ "$(printf '%s\n%s\n' "$GLIBC_FLOOR" "$NEWEST" | sort -V | tail -n 1)" != "$GLIBC_FLOOR" ]; then
    echo "ERROR: ${NEWEST_GLIBC% GLIBC_*} needs glibc $NEWEST (> $GLIBC_FLOOR)" >&2
    exit 1
  fi
  echo "    newest glibc required: $NEWEST (floor $GLIBC_FLOOR)"
fi

echo "[4/6] Application files"
cp "$ROOT_DIR/main.py" "$ROOT_DIR/desktop_app.py" "$ROOT_DIR/LICENSE" "$APP_DIR/app/"
cp -r "$ROOT_DIR/gtoolbox" "$ROOT_DIR/templates" "$ROOT_DIR/static" "$APP_DIR/app/"
find "$APP_DIR/app" -name "__pycache__" -type d -prune -exec rm -rf {} +
rm -f "$APP_DIR/app/static/css/tailwind.input.css"

echo "[5/6] Desktop integration"
cp "$ROOT_DIR/g-toolbox.desktop" "$APP_DIR/g-toolbox.desktop"
cp "$ROOT_DIR/g-toolbox.desktop" "$APP_DIR/usr/share/applications/"
cp "$ROOT_DIR/static/icon.png" "$APP_DIR/g-toolbox.png"
cp "$ROOT_DIR/static/icon.png" "$APP_DIR/usr/share/icons/hicolor/64x64/apps/g-toolbox.png"
ln -sf g-toolbox.png "$APP_DIR/.DirIcon"
# AppStream metadata (software centres, AppImageHub), version from gtoolbox/__init__.py
APP_VERSION="$(sed -n 's/^__version__ = "\(.*\)"/\1/p' "$ROOT_DIR/gtoolbox/__init__.py")"
RELEASE_DATE="$(git -C "$ROOT_DIR" log -1 --format=%cs 2>/dev/null || date -u +%F)"
mkdir -p "$APP_DIR/usr/share/metainfo"
sed -e "s/@VERSION@/$APP_VERSION/" -e "s/@DATE@/$RELEASE_DATE/" \
    "$ROOT_DIR/packaging/linux/g-toolbox.appdata.xml" > "$APP_DIR/usr/share/metainfo/io.github.gorkem_taha.g_toolbox.appdata.xml"
# Same checks as the AppImageHub catalogue test (code/appdir-lint.sh) when the tools exist
if command -v desktop-file-validate >/dev/null; then
  desktop-file-validate "$APP_DIR/g-toolbox.desktop"
fi
if command -v appstreamcli >/dev/null; then
  appstreamcli validate-tree --no-net "$APP_DIR"
fi

cat > "$APP_DIR/AppRun" <<'EOF'
#!/usr/bin/env bash
# G-Toolbox AppImage entry point
HERE="$(dirname "$(readlink -f "$0")")"
DATA="${XDG_DATA_HOME:-$HOME/.local/share}/g-toolbox"
mkdir -p "$DATA"
export GTOOLBOX_DATA_DIR="$DATA"                    # uploads, settings, models (writable)
export GTOOLBOX_PIP_TARGET="$DATA/site-packages"    # on-demand AI libraries
export PATH="$HERE/usr/bin:$PATH"                   # bundled ffmpeg/ffprobe
export PYTHONNOUSERSITE=1
export PYTHONDONTWRITEBYTECODE=1
unset PYTHONHOME PYTHONPATH
cd "$HERE/app"
exec "$HERE/usr/python/bin/python3" "$HERE/app/desktop_app.py" "$@"
EOF
chmod +x "$APP_DIR/AppRun"

echo "[6/6] Packaging"
APPIMAGETOOL="$CACHE_DIR/appimagetool-${APPIMAGETOOL_VERSION}-x86_64.AppImage"
fetch "https://github.com/AppImage/appimagetool/releases/download/${APPIMAGETOOL_VERSION}/appimagetool-x86_64.AppImage" \
      "$APPIMAGETOOL" "$APPIMAGETOOL_SHA256"
chmod +x "$APPIMAGETOOL"
RUNTIME="$CACHE_DIR/runtime-${RUNTIME_TAG}-x86_64"
fetch "https://github.com/AppImage/type2-runtime/releases/download/${RUNTIME_TAG}/runtime-x86_64" \
      "$RUNTIME" "$RUNTIME_SHA256"
OUT="$OUTPUT_DIR/G-Toolbox-x86_64.AppImage"
# Extract-and-run avoids needing FUSE on CI runners / containers; the pinned
# runtime stops appimagetool from downloading the rolling "continuous" one.
# Update information lets AppImageUpdate fetch only the changed blocks of a new
# release; it also writes $OUT.zsync, which must be uploaded with the release.
UPDATE_INFO="gh-releases-zsync|Gorkem-Taha|G-Toolbox|latest|G-Toolbox-x86_64.AppImage.zsync"
(cd "$OUTPUT_DIR" && ARCH=x86_64 "$APPIMAGETOOL" --appimage-extract-and-run --no-appstream \
    --runtime-file "$RUNTIME" -u "$UPDATE_INFO" "$APP_DIR" "$OUT" >/dev/null)
chmod +x "$OUT"

echo "=========================================================="
echo " ✅ $(du -h "$OUT" | cut -f1)  $OUT"
[ -f "$OUT.zsync" ] && echo "    + $OUT.zsync (update information: $UPDATE_INFO)"
echo "=========================================================="
