# wait-for-oneagent.sh
#!/bin/sh
set -e

ONEAGENT_LIB="/opt/dynatrace/oneagent/nonprod/agent/lib64/liboneagentproc.so"
MAX_WAIT=60
WAIT_COUNT=0

echo "[MainApp] Waiting for OneAgent library..."

while [ ! -f "${ONEAGENT_LIB}" ] && [ ${WAIT_COUNT} -lt ${MAX_WAIT} ]; do
    echo "[MainApp] OneAgent not ready, waiting... (${WAIT_COUNT}/${MAX_WAIT})"
    sleep 1
    WAIT_COUNT=$((WAIT_COUNT + 1))
done

if [ ! -f "${ONEAGENT_LIB}" ]; then
    echo "[MainApp] ERROR: OneAgent library not found after ${MAX_WAIT}s" >&2
    exit 1
fi

echo "[MainApp] OneAgent ready! Starting application with LD_PRELOAD=${LD_PRELOAD}"
exec "$@"
# =============================================================================

#!/bin/sh
set -e

ONEAGENT_LIB="/opt/dynatrace/oneagent/nonprod/agent/lib64/liboneagentproc.so"
MAX_WAIT=60
WAIT_COUNT=0

echo "[MainApp] Waiting for OneAgent library..."

while [ ! -f "${ONEAGENT_LIB}" ] && [ ${WAIT_COUNT} -lt ${MAX_WAIT} ]; do
    echo "[MainApp] OneAgent not ready, waiting... (${WAIT_COUNT}/${MAX_WAIT})"
    sleep 1
    WAIT_COUNT=$((WAIT_COUNT + 1))
done

if [ ! -f "${ONEAGENT_LIB}" ]; then
    echo "[MainApp] ERROR: OneAgent library not found after ${MAX_WAIT}s" >&2
    exit 1
fi

echo "[MainApp] OneAgent library found."
echo "[MainApp] DT Environment Variables:"
env | grep '^DT_' || echo "[MainApp] No DT_* environment variables set."

echo "[MainApp] LD_PRELOAD: ${LD_PRELOAD}"
echo "[MainApp] Checking OneAgent instrumentation..."

if [ -n "$LD_PRELOAD" ] && echo "$LD_PRELOAD" | grep -q "oneagent"; then
    echo "[MainApp] LD_PRELOAD appears correctly set for OneAgent."
else
    echo "[MainApp] WARNING: LD_PRELOAD does NOT contain OneAgent library!"
fi

# Optionally, check if we can access library symbols (diagnostic only)
if [ -f "${ONEAGENT_LIB}" ]; then
    if command -v ldd > /dev/null; then
        ldd "${ONEAGENT_LIB}" || echo "[MainApp] ldd failed on ${ONEAGENT_LIB}"
    fi
fi

echo "[MainApp] Starting application: $@"
exec "$@"

