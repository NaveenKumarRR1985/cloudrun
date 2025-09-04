FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install OpenTelemetry auto-instrumentation packages
RUN pip install --no-cache-dir \
    opentelemetry-distro[otlp]==0.45b0 \
    opentelemetry-instrumentation-flask==0.45b0 \
    opentelemetry-instrumentation-requests==0.45b0 \
    opentelemetry-instrumentation-logging==0.45b0 \
    opentelemetry-instrumentation-urllib3 \
    opentelemetry-propagator-b3 \
    opentelemetry-propagator-jaeger \
    opentelemetry-sdk \
    opentelemetry-api

# Auto-install instrumentation packages
RUN opentelemetry-bootstrap --action=install

# Copy application code
COPY app/ .

# Set environment variables for auto-instrumentation
ENV OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true
ENV OTEL_SERVICE_NAME="ecommerce-demo"
ENV OTEL_SERVICE_VERSION="1.0.0"

# Expose port
EXPOSE 8080

# Use opentelemetry-instrument to run the app with auto-instrumentation
CMD ["opentelemetry-instrument", "gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--timeout", "120", "app:app"]
