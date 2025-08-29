FROM otel/opentelemetry-collector-contrib:0.91.0
COPY config.yaml /etc/otelcol-contrib/config.yaml
EXPOSE 5517 5518 8889 13133 1777 55679
CMD ["--config=/etc/otelcol-contrib/config.yaml"]
