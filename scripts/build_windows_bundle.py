#!/usr/bin/env python3
"""Builds the portable Windows bundle: dist/G-Toolbox-v<version>-Windows.zip

Contents (inside a top-level "G-Toolbox/" folder):
  G-Toolbox.exe (launcher, built from launcher/ with the .NET SDK), main.py,
  desktop_app.py, gtoolbox/, templates/, static/, requirements-desktop.lock,
  requirements-ai.txt, LICENSE, README.md, THIRD_PARTY_NOTICES.md

The zip is reproducible: fixed timestamps, sorted entries, no caches.
Usage: python scripts/build_windows_bundle.py [--exe path/to/G-Toolbox.exe]
       (without --exe the launcher is built with `dotnet build`)
"""
import argparse
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXED_TIME = (2020, 1, 1, 0, 0, 0)
FILES = ["main.py", "desktop_app.py", "requirements-desktop.lock", "requirements-ai.txt",
         "LICENSE", "README.md", "THIRD_PARTY_NOTICES.md"]
DIRS = ["gtoolbox", "templates", "static"]
EXCLUDE = {"__pycache__", ".DS_Store"}
EXCLUDE_FILES = {"static/css/tailwind.input.css"}


def version() -> str:
    text = (ROOT / "gtoolbox" / "__init__.py").read_text(encoding="utf-8")
    return re.search(r'__version__\s*=\s*"([^"]+)"', text).group(1)


def build_launcher(out_dir: Path) -> Path:
    subprocess.run(["dotnet", "build", str(ROOT / "launcher" / "G-Toolbox.Launcher.csproj"),
                    "-c", "Release", "-o", str(out_dir), "--nologo"], check=True)
    return out_dir / "G-Toolbox.exe"


def add(zf: zipfile.ZipFile, src: Path, arcname: str) -> None:
    info = zipfile.ZipInfo(arcname, FIXED_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    zf.writestr(info, src.read_bytes())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", type=Path, help="prebuilt G-Toolbox.exe (skips dotnet build)")
    args = ap.parse_args()

    ver = version()
    out = ROOT / "dist" / f"G-Toolbox-v{ver}-Windows.zip"
    out.parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        exe = args.exe or build_launcher(Path(tmp))
        entries = {"G-Toolbox.exe": exe}
        for f in FILES:
            entries[f] = ROOT / f
        for d in DIRS:
            for p in (ROOT / d).rglob("*"):
                rel = p.relative_to(ROOT).as_posix()
                if p.is_file() and not (set(p.parts) & EXCLUDE) and rel not in EXCLUDE_FILES:
                    entries[rel] = p
        missing = [k for k, v in entries.items() if not v.is_file()]
        if missing:
            print("missing files:", ", ".join(missing), file=sys.stderr)
            return 1
        with zipfile.ZipFile(out, "w") as zf:
            for rel in sorted(entries):
                add(zf, entries[rel], f"G-Toolbox/{rel}")
    print(f"{out} ({out.stat().st_size / 1e6:.1f} MB, {len(entries)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
