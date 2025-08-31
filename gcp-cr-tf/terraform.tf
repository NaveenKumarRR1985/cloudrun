# Dynatrace API Token Secret
resource "google_secret_manager_secret" "dynatrace_api_token" {
  secret_id = "dynatrace-api-token"
  
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "dynatrace_api_token_version" {
  secret      = google_secret_manager_secret.dynatrace_api_token.id
  secret_data = var.dynatrace_api_token
}

# OpenTelemetry Collector Configuration Secret
resource "google_secret_manager_secret" "otel_config" {
  secret_id = "otel-collector-config"
  
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "otel_config_version" {
  secret   = google_secret_manager_secret.otel_config.id
  secret_data = templatefile("${path.module}/config.yaml", {
    dynatrace_endpoint = var.dynatrace_endpoint
  })
}

# Cloud Run Service
resource "google_cloud_run_v2_service" "google_otel_cloud_run_sample" {
  name     = "google-otel-cloud-run-sample"
  location = var.region

  template {
    # Container dependencies annotation
    annotations = {
      "run.googleapis.com/container-dependencies" = jsonencode({
        app = ["collector"]
      })
    }

    # Secret volume configuration
    volumes {
      name = "config"
      secret {
        secret = google_secret_manager_secret.otel_config.secret_id
        items {
          key  = "latest"
          path = "config.yaml"
        }
      }
    }

    # Collector container - starts first
    containers {
      name  = "collector"
      image = "us-docker.pkg.dev/cloud-ops-agents-artifacts/google-cloud-opentelemetry-collector/otelcol-google:0.131.0"
      
      args = ["--config=/etc/otelcol-google/config.yaml"]

      env {
        name = "DT_API_TOKEN"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.dynatrace_api_token.secret_id
            version = "latest"
          }
        }
      }

      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }

      startup_probe {
        http_get {
          path = "/"
          port = 13133
        }
        timeout_seconds = 30
        period_seconds  = 30
      }

      liveness_probe {
        http_get {
          path = "/"
          port = 13133
        }
        timeout_seconds = 30
        period_seconds  = 30
      }

      volume_mounts {
        name       = "config"
        mount_path = "/etc/otelcol-google/"
      }
    }

    # App container - depends on collector
    containers {
      name  = "app"
      image = var.app_image
      
      # This container depends on the collector container
      depends_on = ["collector"]

      ports {
        container_port = 8080
      }

      env {
        name  = "OTEL_EXPORTER_OTLP_ENDPOINT"
        value = "http://localhost:4317"
      }

      startup_probe {
        http_get {
          path = "/health"  # Adjust path as needed for your app's health endpoint
          port = 8080
        }
        timeout_seconds = 30
        period_seconds  = 10
        failure_threshold = 3
      }

      liveness_probe {
        http_get {
          path = "/health"  # Adjust path as needed for your app's health endpoint
          port = 8080
        }
        timeout_seconds = 30
        period_seconds  = 30
      }
    }
  }

  # Launch stage annotation
  metadata {
    annotations = {
      "run.googleapis.com/launch-stage" = "ALPHA"
    }
  }
}

# IAM binding to allow Cloud Run to access secrets
resource "google_secret_manager_secret_iam_member" "dynatrace_token_access" {
  secret_id = google_secret_manager_secret.dynatrace_api_token.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "config_access" {
  secret_id = google_secret_manager_secret.otel_config.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# Service Account for Cloud Run
resource "google_service_account" "cloud_run_sa" {
  account_id   = "cloud-run-otel-sa"
  display_name = "Cloud Run OpenTelemetry Service Account"
}

# IAM binding for Cloud Run service to use the service account
resource "google_cloud_run_v2_service_iam_member" "cloud_run_sa_binding" {
  name     = google_cloud_run_v2_service.google_otel_cloud_run_sample.name
  location = google_cloud_run_v2_service.google_otel_cloud_run_sample.location
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# Variables
variable "region" {
  description = "The region to deploy the Cloud Run service"
  type        = string
  default     = "us-central1"
}

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "app_image" {
  description = "Container image for the application"
  type        = string
  default     = "my-app"
}

variable "dynatrace_api_token" {
  description = "Dynatrace API Token with OTLP ingest permissions"
  type        = string
  sensitive   = true
}

variable "dynatrace_endpoint" {
  description = "Dynatrace OTLP endpoint URL"
  type        = string
  # Example: "https://abc12345.live.dynatrace.com/api/v2/otlp"
}

# Outputs
output "service_url" {
  description = "URL of the Cloud Run service"
  value       = google_cloud_run_v2_service.google_otel_cloud_run_sample.uri
}

output "service_account_email" {
  description = "Email of the service account used by Cloud Run"
  value       = google_service_account.cloud_run_sa.email
}