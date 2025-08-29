FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# non-root user as before
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app
EXPOSE 8080

# OpenTelemetry exporter settings – point to local side-car
ENV OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
ENV OTEL_EXPORTER_OTLP_PROTOCOL=grpc
ENV OTEL_RESOURCE_ATTRIBUTES=service.name=dynatrace-test-app

# health-check unchanged
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

CMD ["opentelemetry-instrument",
     "gunicorn",
     "--bind", "0.0.0.0:8080",
     "--workers", "2",
     "--timeout", "120",
     "--keep-alive", "2",
     "app:app"]
