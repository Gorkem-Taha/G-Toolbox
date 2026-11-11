#!/usr/bin/env bash
# Regenerates the hash-pinned lock files from requirements-*.txt.
# The locks are "universal": one file covers Windows/Linux/macOS and Python 3.10+.
# Requires uv (https://docs.astral.sh/uv/). Commit the resulting *.lock files.
set -euo pipefail
cd "$(dirname "$0")/.."
for name in core desktop dev; do
  uv pip compile --quiet --universal --python-version 3.10 --generate-hashes --no-header \
     --output-file "requirements-$name.lock" "requirements-$name.txt"
  echo "requirements-$name.lock: $(grep -cE '^[a-z]' "requirements-$name.lock") packages"
done
