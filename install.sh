#!/usr/bin/env bash
# AZMail one-click install. Counted download via this project's Worker.
# Usage: curl -fsSL https://azmail-download-tracker.vibelock.workers.dev/install.sh | bash
set -euo pipefail

HOST="${AZMAIL_HOST:-https://azmail-download-tracker.vibelock.workers.dev}"
ASSET="${AZMAIL_ASSET:-azmail-0.1.0.tar.gz}"
WORKDIR="${AZMAIL_HOME:-$HOME/azmail}"

mkdir -p "$WORKDIR"
cd "$WORKDIR"

echo "Downloading counted tarball from ${HOST}/download (User-Agent Mozilla/5.0)…"
curl -fsSL -A 'Mozilla/5.0' "${HOST}/download?asset=${ASSET}" -o "${ASSET}"

tar -xzf "${ASSET}"
DIR="$(find . -maxdepth 1 -type d -name 'azmail-*' | head -n 1)"
if [ -n "${DIR}" ]; then
  cd "${DIR}"
fi

python3 -m venv .venv
# shellcheck disable=SC1091
. .venv/bin/activate
python -m pip install -U pip
python -m pip install -e .

echo
echo "Installed AZMail."
echo "Run: azmail ui"
echo "Then open http://127.0.0.1:8876 (loopback only)"
echo "v0.1 does not send internet email. Author: Aziel Eliab."
