FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install OpenTelemetry auto-instrumentation
RUN pip install --no-cache-dir \
    opentelemetry-distro[otlp] \
    opentelemetry-instrumentation

# Auto-instrument
RUN opentelemetry-bootstrap -a install

# Copy application
COPY app.py .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

EXPOSE 8080

# Start with OpenTelemetry auto-instrumentation
CMD exec opentelemetry-instrument \
    --traces_exporter otlp \
    --metrics_exporter otlp \
    --logs_exporter otlp \
    gunicorn --bind 0.0.0.0:8080 --workers 2 --timeout 120 app:app