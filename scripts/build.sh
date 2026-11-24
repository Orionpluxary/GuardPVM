#!/usr/bin/env bash
# =============================================================================
# FILE PURPOSE:
# Automated source build script for the GuardPVM custom CPython interpreter.
# Applies GuardPVM core patches onto CPython 3.16 source tree, compiles with
# multi-threaded optimizations, and installs into /opt/guard-pvm.
# Run with: bash scripts/build.sh
# =============================================================================

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CPYTHON_SRC="${CPYTHON_SRC:-${HOME}/guard-pvm-project/cpython-guardpvm}"
INSTALL_PREFIX="${INSTALL_PREFIX:-/opt/guard-pvm}"
JOBS="${JOBS:-$(nproc 2>/dev/null || echo 4)}"

echo "========================================================="
echo " GuardPVM Source Compiler & Build Automation"
echo "========================================================="
echo "Source Tree   : ${CPYTHON_SRC}"
echo "Install Prefix: ${INSTALL_PREFIX}"
echo "Build Threads : ${JOBS}"
echo "========================================================="

if [ ! -d "${CPYTHON_SRC}" ]; then
    echo "Directory ${CPYTHON_SRC} not found. Cloning CPython main..."
    mkdir -p "$(dirname "${CPYTHON_SRC}")"
    git clone --depth 1 https://github.com/python/cpython.git "${CPYTHON_SRC}"
fi

echo "[1/4] Syncing GuardPVM core patches into CPython tree..."
cp -v "${ROOT_DIR}/src/core/Include/internal/pycore_guardpvm.h" "${CPYTHON_SRC}/Include/internal/"
cp -v "${ROOT_DIR}/src/core/Python/ceval_macros.h"              "${CPYTHON_SRC}/Python/"
cp -v "${ROOT_DIR}/src/core/Python/bytecodes.c"                 "${CPYTHON_SRC}/Python/"
cp -v "${ROOT_DIR}/src/core/Python/guardpvm.c"                  "${CPYTHON_SRC}/Python/"
cp -v "${ROOT_DIR}/src/core/Python/sysmodule.c"                 "${CPYTHON_SRC}/Python/"
cp -v "${ROOT_DIR}/src/core/Python/pylifecycle.c"               "${CPYTHON_SRC}/Python/"
cp -v "${ROOT_DIR}/src/core/Python/getversion.c"                "${CPYTHON_SRC}/Python/"

cd "${CPYTHON_SRC}"

echo "[2/4] Configuring build..."
./configure --prefix="${INSTALL_PREFIX}" --enable-optimizations --with-ensurepip=install

echo "[3/4] Compiling GuardPVM CPython engine (using ${JOBS} cores)..."
make -j"${JOBS}"

echo "[4/4] Installing into ${INSTALL_PREFIX}..."
sudo make install

echo "Configuring symlinks..."
sudo ln -sf "${INSTALL_PREFIX}/bin/python3.16" /usr/local/bin/guard-python

echo "=== Build Complete! Verifying GuardPVM version: ==="
/usr/local/bin/guard-python --version
