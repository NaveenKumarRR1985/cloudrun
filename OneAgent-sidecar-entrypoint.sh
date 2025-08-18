#!/bin/sh
# POSIX shell (dash compatible, no bashisms)
set -eu

DT_DIR="${DT_DIR:-/opt/dynatrace}"
ZIP_PATH="${ZIP_PATH:-/image/oneagent.zip}"
DT_STAGE="${DT_STAGE:-nonprod}"
HEALTH_PORT="${HEALTH_PORT:-8082}"
HEALTH_PATH="${HEALTH_PATH:-/healthz}"

TARGET_ROOT="${DT_DIR}/oneagent/${DT_STAGE}/agent"
TARGET_LIB64="${TARGET_ROOT}/lib64"
TARGET_LIB="${TARGET_LIB64}/liboneagentproc.so"

echo "[OneAgent] DT_DIR=${DT_DIR} DT_STAGE=${DT_STAGE}"

mkdir -p "${DT_DIR}"

# ---- Extract ZIP if target lib not already present ----
if [ ! -e "${TARGET_LIB}" ]; then
  echo "[OneAgent] Extracting OneAgent into ${DT_DIR}..."
  python3 - <<'PY'
import os, zipfile
dt_dir   = os.environ.get("DT_DIR", "/opt/dynatrace")
zip_path = os.environ.get("ZIP_PATH", "/image/oneagent.zip")
with zipfile.ZipFile(zip_path) as z:
    z.extractall(dt_dir)
PY

  # Explicitly find the real 64-bit library, not the 32-bit one
  REAL_LIB="$(find "${DT_DIR}" -path "*/agent/lib64/liboneagentproc.so" -type f | head -n1 || true)"
  if [ -z "${REAL_LIB}" ]; then
    echo "[OneAgent] ERROR: 64-bit liboneagentproc.so not found in extracted ZIP." >&2
    exit 1
  fi

  # Create stable preload path
  mkdir -p "${TARGET_LIB64}"
  rm -f "${TARGET_LIB}"
  ln -s "${REAL_LIB}" "${TARGET_LIB}"

  chmod -R a+rX "${DT_DIR}"
  echo "[OneAgent] Ready. ${TARGET_LIB} -> ${REAL_LIB}"
else
  echo "[OneAgent] Reusing existing ${TARGET_LIB}"
fi

# ---- Minimal health server ----
echo "[OneAgent] Starting health server on :${HEALTH_PORT}${HEALTH_PATH}"

exec python3 - <<PY
from http.server import BaseHTTPRequestHandler, HTTPServer
import os, sys
PORT = int(os.environ.get("HEALTH_PORT", "8082"))
PATH = os.environ.get("HEALTH_PATH", "/healthz")
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == PATH:
            self.send_response(200); self.end_headers(); self.wfile.write(b"ok")
        else:
            self.send_response(404); self.end_headers()
    def log_message(self, *args): pass
try:
    HTTPServer(("0.0.0.0", PORT), H).serve_forever()
except Exception as e:
    sys.stderr.write(f"[OneAgent] Health server failed: {e}\\n"); sys.exit(1)
PY
