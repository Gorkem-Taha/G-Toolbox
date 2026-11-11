#!/usr/bin/env python3
"""Creates and signs the checksum manifest for a G-Toolbox release.

Usage:
    python scripts/sign_release.py Releases/ [--key ~/.config/g-toolbox/release-signing-key.pem]

Writes <dir>/SHA256SUMS and <dir>/SHA256SUMS.sig. Upload both to the GitHub
release together with the files they list; the in-app updater refuses any
release whose manifest is missing or not signed by the key embedded in
main.py (UPDATE_PUBLIC_KEY_B64).

The private key must never be committed. Back it up offline: if it is lost,
users can only move to a new key by installing a release manually.
"""
import argparse
import base64
import hashlib
import sys
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

DEFAULT_KEY = Path.home() / ".config" / "g-toolbox" / "release-signing-key.pem"
SKIP = {"SHA256SUMS", "SHA256SUMS.sig", "README.md"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("release_dir", type=Path)
    ap.add_argument("--key", type=Path, default=DEFAULT_KEY)
    args = ap.parse_args()

    files = sorted(p for p in args.release_dir.iterdir() if p.is_file() and p.name not in SKIP)
    if not files:
        print("No release files found.", file=sys.stderr)
        return 1

    manifest = "".join(f"{sha256(p)}  {p.name}\n" for p in files).encode("utf-8")
    key = serialization.load_pem_private_key(args.key.read_bytes(), password=None)
    if not isinstance(key, Ed25519PrivateKey):
        print("Key is not an ed25519 private key.", file=sys.stderr)
        return 1
    signature = key.sign(manifest)

    (args.release_dir / "SHA256SUMS").write_bytes(manifest)
    (args.release_dir / "SHA256SUMS.sig").write_bytes(signature)
    pub = key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    print(manifest.decode(), end="")
    print(f"\nSigned with public key {base64.b64encode(pub).decode()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
