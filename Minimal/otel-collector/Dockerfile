# Use Alpine instead of the default distroless image
FROM alpine:3.18

# Alternative 1: Try with explicit version and better error handling
RUN apk add --no-cache ca-certificates wget tar && \
    echo "Downloading OpenTelemetry Collector..." && \
    wget -v -O /tmp/otelcol.tar.gz https://github.com/open-telemetry/opentelemetry-collector-releases/releases/download/v0.132.4/otelcol-contrib_0.132.4_linux_amd64.tar.gz && \
    echo "Extracting..." && \
    tar -tzf /tmp/otelcol.tar.gz && \
    tar -xzf /tmp/otelcol.tar.gz -C /tmp/ && \
    ls -la /tmp/ && \
    mv /tmp/otelcol-contrib /usr/local/bin/ && \
    chmod +x /usr/local/bin/otelcol-contrib && \
    rm /tmp/otelcol.tar.gz

# Install your tools
RUN apk add --no-cache jq curl less nano

# Create non-root user first
RUN adduser -D otelcol

# Create telemetry directory with proper ownership
RUN mkdir -p /home/otelcol/telemetry && \
    chown -R otelcol:otelcol /home/otelcol/telemetry

# Copy configuration
COPY config.yaml /etc/otel-collector-config.yaml

# Switch to non-root user
USER otelcol

# Set working directory
WORKDIR /home/otelcol

# Expose ports
EXPOSE 4317 4318 13133

# Set the command
ENTRYPOINT ["/usr/local/bin/otelcol-contrib"]
CMD ["--config=/etc/otel-collector-config.yaml"]