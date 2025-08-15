#!/bin/sh
# POSIX sh (no pipefail)
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

# Ensure mount path exists (Cloud Run will mount tmpfs here)
mkdir -p "${DT_DIR}"

# Extract and prepare fixed path only if not already present
if [ ! -e "${TARGET_LIB}" ]; then
  echo "[OneAgent] Extracting OneAgent into ${DT_DIR}..."
  python3 - <<'PY'
import os, zipfile, sys, shutil, stat

dt_dir    = os.environ.get("DT_DIR", "/opt/dynatrace")
zip_path  = os.environ.get("ZIP_PATH", "/image/oneagent.zip")
stage     = os.environ.get("DT_STAGE", "nonprod")
target_lib = os.path.join(dt_dir, "oneagent", stage, "agent", "lib64", "liboneagentproc.so")

# extract zip
with zipfile.ZipFile(zip_path) as z:
    z.extractall(dt_dir)

# # locate actual lib
# real_lib = None
# for root, _, files in os.walk(dt_dir):
#     if "liboneagentproc.so" in files:
#         real_lib = os.path.join(root, "liboneagentproc.so")
#         break
# if not real_lib:
#     sys.stderr.write("[OneAgent] ERROR: liboneagentproc.so not found after extraction.\n")
#     sys.exit(1)

# # ensure requested path exists
# os.makedirs(os.path.dirname(target_lib), exist_ok=True)

# # try to symlink; if FS disallows, copy
# try:
#     if os.path.lexists(target_lib):
#         os.remove(target_lib)
#     os.symlink(real_lib, target_lib)
# except OSError:
#     shutil.copy2(real_lib, target_lib)

# make world-readable so any UID in app container can load it
for root, dirs, files in os.walk(dt_dir):
    for d in dirs:
        os.chmod(os.path.join(root, d), 0o755)
    for f in files:
        os.chmod(os.path.join(root, f), 0o644)

print(f"[OneAgent] Ready. {target_lib}")
PY
else
  echo "[OneAgent] Reusing existing ${TARGET_LIB}"
fi

# Minimal HTTP health server (starts AFTER the agent is ready)
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
    sys.stderr.write(f"[OneAgent] Health server failed: {e}\n"); sys.exit(1)
PY
