FROM otel/opentelemetry-collector-contrib:0.91.0

# Copy the collector configuration
COPY config.yaml /etc/otelcol-contrib/config.yaml

# Expose ports
EXPOSE 4317 4318 8888 13133 1777 55679

# Use the custom configuration
CMD ["--config=/etc/otelcol-contrib/config.yaml"]
