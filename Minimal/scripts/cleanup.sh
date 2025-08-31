#!/bin/bash

COLLECTOR_CONTAINER=$(docker-compose ps -q otel-collector)

if [ -z "$COLLECTOR_CONTAINER" ]; then
    echo "Error: OTEL Collector container not running"
    exit 1
fi

echo "Recent traces:"
echo "=============="

# Show recent traces with pretty formatting
docker exec $COLLECTOR_CONTAINER sh -c '
if [ -f /tmp/telemetry/traces.jsonl ]; then
    echo "Last 5 traces:"
    tail -5 /tmp/telemetry/traces.jsonl | while read line; do
        echo "$line" | jq -r ".resourceSpans[0].scopeSpans[0].spans[0] | \"Trace: \(.name) | Duration: \(.endTimeUnixNano - .startTimeUnixNano)ns | Status: \(.status.code // \"OK\")\""
        echo "---"
    done
else
    echo "No trace data found yet. Generate some by calling your app endpoints."
fi
'