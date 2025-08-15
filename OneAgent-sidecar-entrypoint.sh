#!/usr/bin/env sh
set -euo pipefail

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

  REAL_LIB="$(find "${DT_DIR}" -type f -name 'liboneagentproc.so' | head -n 1 || true)"
  if [ -z "${REAL_LIB}" ]; then
    echo "[OneAgent] ERROR: liboneagentproc.so not found after extraction." >&2
    exit 1
  fi

  mkdir -p "${TARGET_LIB64}"
  ln -sf "${REAL_LIB}" "${TARGET_LIB}"
  chmod -R a+rX "${DT_DIR}"
  echo "[OneAgent] Ready. ${TARGET_LIB} -> ${REAL_LIB}"
else
  echo "[OneAgent] Reusing existing ${TARGET_LIB}"
fi

# ---- startup probe server (starts only after extraction succeeds) ----
: "${HEALTH_PORT:=8082}"
: "${HEALTH_PATH:=/healthz}"
echo "[OneAgent] Starting health server on :${HEALTH_PORT}${HEALTH_PATH}"

exec python3 - <<PY
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
PORT = int(os.environ.get("HEALTH_PORT", "8082"))
PATH = os.environ.get("HEALTH_PATH", "/healthz")
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == PATH:
            self.send_response(200); self.end_headers(); self.wfile.write(b"ok")
        else:
            self.send_response(404); self.end_headers()
    def log_message(self, *args): pass
HTTPServer(("0.0.0.0", PORT), H).serve_forever()
PY
