variable "project" {
  description = "GCP project id"
  type        = string
}

variable "region" {
  description = "GCP region for Cloud Run and Artifact Registry"
  type        = string
  default     = "us-central1"
}

variable "service_name" {
  description = "Cloud Run service name"
  type        = string
  default     = "ospsd-service"
}

variable "artifact_repo" {
  description = "Artifact Registry repository id"
  type        = string
  default     = "oss-repo"
}

variable "image" {
  description = "Container image URL (Artifact Registry)"
  type        = string
  default     = ""
}

variable "telemetry_export_path" {
  description = "Path used by the app for telemetry output inside container"
  type        = string
  default     = "/app/telemetry/metrics.json"
}
