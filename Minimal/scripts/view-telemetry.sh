#!/bin/bash

COLLECTOR_CONTAINER=$(docker-compose ps -q otel-collector)

if [ -z "$COLLECTOR_CONTAINER" ]; then
    echo "Error: OTEL Collector container not running"
    echo "Run: ./scripts/start.sh"
    exit 1
fi

echo "Connecting to OTEL Collector container..."
echo "Available commands inside container:"
echo "  ls /home/otelcol/telemetry/                    # List telemetry files"
echo "  cat /home/otelcol/telemetry/traces.jsonl       # View raw traces"
echo "  cat /home/otelcol/telemetry/metrics.jsonl      # View raw metrics" 
echo "  cat /home/otelcol/telemetry/logs.jsonl         # View raw logs"
echo "  tail -f /home/otelcol/telemetry/all-telemetry.jsonl  # Watch live data"
echo "  jq . /home/otelcol/telemetry/traces.jsonl      # Pretty print traces"
echo "  grep 'cpu-intensive' /home/otelcol/telemetry/traces.jsonl  # Filter traces"
echo ""
echo "Type 'exit' to leave the container"
echo ""

# Enter the container with shell access
docker exec -it $COLLECTOR_CONTAINER cat /home/otelcol/telemetry/traces.jsonl