#!/usr/bin/env sh
set -euo pipefail

# Shared tmpfs mounted in BOTH containers
DT_DIR="${DT_DIR:-/opt/dynatrace}"
ZIP_PATH="${ZIP_PATH:-/image/oneagent.zip}"
DT_STAGE="${DT_STAGE:-nonprod}"

TARGET_ROOT="${DT_DIR}/oneagent/${DT_STAGE}/agent"
TARGET_LIB64="${TARGET_ROOT}/lib64"
TARGET_LIB="${TARGET_LIB64}/liboneagentproc.so"

echo "[OneAgent] DT_DIR=${DT_DIR}  DT_STAGE=${DT_STAGE}"
mkdir -p "${DT_DIR}"

if [ ! -e "${TARGET_LIB}" ]; then
  echo "[OneAgent] Extracting OneAgent into ${DT_DIR}..."
  python3 - <<'PY'
import os, zipfile
zip_path = os.environ.get("ZIP_PATH", "/image/oneagent.zip")
dest = os.environ.get("DT_DIR", "/opt/dynatrace")
with zipfile.ZipFile(zip_path) as z:
    z.extractall(dest)
PY

  # Find the real library from whatever versioned path the ZIP created
  REAL_LIB="$(find "${DT_DIR}" -type f -name 'liboneagentproc.so' | head -n 1 || true)"
  if [ -z "${REAL_LIB}" ]; then
    echo "[OneAgent] ERROR: liboneagentproc.so not found after extraction." >&2
    exit 1
  fi

  # Ensure requested path exists, then symlink the actual lib to your fixed path
  mkdir -p "${TARGET_LIB64}"
  ln -sf "${REAL_LIB}" "${TARGET_LIB}"

  # (Optional safety) also provide a flat alias if you ever want to use it
  ln -sf "${REAL_LIB}" "${DT_DIR}/liboneagentproc.so"

  chmod -R a+rX "${DT_DIR}"
  echo "[OneAgent] Ready. ${TARGET_LIB} -> ${REAL_LIB}"
else
  echo "[OneAgent] Reusing existing ${TARGET_LIB}"
fi

# Keep sidecar alive
tail -f /dev/null
