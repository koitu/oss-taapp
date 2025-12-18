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

variable "no_auth" {
  description = "Disable authentication"
  type        = string
  default     = "true"
}

variable "trello_board_id" {
  description = "Optional Trello board ID"
  type        = string
  default     = ""
}

variable "credentials_file" {
  description = "Path to the GCP service account key file"
  type        = string
}
