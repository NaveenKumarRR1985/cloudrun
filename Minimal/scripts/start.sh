#!/bin/bash
set -e

echo "Starting minimal OpenTelemetry local setup..."

# Build and start services
docker-compose up --build -d

echo "Waiting for services to start..."
sleep 10

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    echo "Services started successfully!"
    echo ""
    echo "Flask App: http://localhost:8080"
    echo "OTEL Collector container: $(docker-compose ps -q otel-collector)"
    echo ""
    echo "To view telemetry data:"
    echo "  ./scripts/view-telemetry.sh"
    echo ""
    echo "To generate test data:"
    echo "  curl http://localhost:8080/cpu-intensive?iterations=10000"
    echo "  curl http://localhost:8080/database-ops?operation=select"
    echo "  curl http://localhost:8080/load-test"
else
    echo "Error: Services failed to start"
    docker-compose logs
fi