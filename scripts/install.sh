#!/usr/bin/env bash
# =============================================================================
# FILE PURPOSE:
# Automated installer script for the GuardPVM execution engine.
# Extracts precompiled GuardPVM runtime binaries or sets up symlinks in /usr/local/bin
# and verifies runtime health.
# Run with: bash scripts/install.sh
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TAR_FILE="${SCRIPT_DIR}/../install/guard-pvm-sdk.tar.gz"
OPT_GUARD="/opt/guard-pvm"

echo "========================================================"
echo " GuardPVM SDK v1.0 Installation Script"
echo "========================================================"

if [ ! -f "${TAR_FILE}" ]; then
    echo "Error: Archive ${TAR_FILE} does not exist!" >&2
    exit 1
fi

echo "[1/3] Extracting GuardPVM SDK archive to /opt/..."
sudo mkdir -p /opt
sudo tar -xzf "${TAR_FILE}" -C /opt

echo "[2/3] Configuring binary links in /opt/guard-pvm and /usr/local/bin..."
sudo ln -sf /opt/guard-pvm/bin/python3.16 /opt/guard-pvm/bin/guard-python
sudo ln -sf /opt/guard-pvm/bin/python3.16 /opt/guard-pvm/bin/python3
sudo ln -sf /opt/guard-pvm/bin/python3.16 /usr/local/bin/guard-python

echo "[3/3] Verifying installation..."
if [ ! -x /usr/local/bin/guard-python ]; then
    echo "Error: /usr/local/bin/guard-python is not executable!" >&2
    exit 1
fi

echo "=== GuardPVM successfully installed! ==="
/usr/local/bin/guard-python --version
echo "Location: $(which guard-python) -> $(readlink -f $(which guard-python))"
