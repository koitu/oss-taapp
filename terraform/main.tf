resource "google_project_service" "required_apis" {
  for_each = toset([
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "iam.googleapis.com",
    "secretmanager.googleapis.com",
    "compute.googleapis.com",
    "vpcaccess.googleapis.com"
  ])
  service = each.key
  disable_on_destroy = false
}

# VPC Network
resource "google_compute_network" "vpc" {
  name                    = "ospsd-vpc"
  auto_create_subnetworks = false

  depends_on = [google_project_service.required_apis]
}

resource "google_compute_subnetwork" "subnet" {
  name          = "ospsd-subnet"
  ip_cidr_range = "10.0.0.0/24"
  region        = var.region
  network       = google_compute_network.vpc.id
}

resource "google_vpc_access_connector" "serverless_connector" {
  name          = "ospsd-connector"
  region        = var.region
  project       = var.project
  network       = google_compute_network.vpc.name
  ip_cidr_range = "10.8.0.0/28"

  depends_on = [google_compute_network.vpc]
}

# Artifact Registry
resource "google_artifact_registry_repository" "repo" {
  provider      = google
  project       = var.project
  location      = var.region
  repository_id = var.artifact_repo
  description   = "Docker repository for ospsd-service"
  format        = "DOCKER"

  depends_on = [google_project_service.required_apis]
}

# Service Account
resource "google_service_account" "cloudrun" {
  account_id   = "ospsd-cloudrun-sa"
  display_name = "Service account for Cloud Run ospsd-service"

  depends_on = [google_project_service.required_apis]
}

resource "google_project_iam_member" "cloudrun_cloudbuild_roles" {
  project = var.project
  role    = "roles/run.admin"
  member  = "serviceAccount:${google_service_account.cloudrun.email}"
}

# Secrets configuration
locals {
  secrets = {
    "DISCORD_CLIENT_ID"     = "DISCORD_CLIENT_ID"
    "DISCORD_CLIENT_SECRET" = "DISCORD_CLIENT_SECRET"
    "DISCORD_PUBLIC_KEY"    = "DISCORD_PUBLIC_KEY"
    "DISCORD_BOT_TOKEN"     = "DISCORD_BOT_TOKEN"
    "OPENAI_API_KEY"        = "OPENAI_API_KEY"
    "CLAUDE_API_KEY"        = "CLAUDE_API_KEY"
    "TRELLO_API_KEY"        = "TRELLO_API_KEY"
    "TRELLO_API_SECRET"     = "TRELLO_API_SECRET"
  }
}

# Reference existing secrets
data "google_secret_manager_secret" "secrets" {
  for_each  = local.secrets
  secret_id = each.key
  project   = var.project
}

# Grant access to existing secrets
resource "google_secret_manager_secret_iam_member" "secret_access" {
  for_each  = local.secrets
  project   = var.project
  secret_id = each.key
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloudrun.email}"
}

resource "google_cloud_run_v2_service" "service" {
  name     = var.service_name
  location = var.region
  ingress = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.cloudrun.email
    timeout = "300s"

    scaling {
      min_instance_count = 1
      max_instance_count = 1
    }

    # always force pull
    revision = "${var.service_name}-${formatdate("YYYYMMDDhhmmss", timestamp())}"

    vpc_access {
      network_interfaces {
        network = google_compute_network.vpc.id
        subnetwork = google_compute_subnetwork.subnet.id
      }
      egress = "PRIVATE_RANGES_ONLY"
    }

    containers {
      image = var.image

      ports {
        name           = "http1"
        container_port = 8000
      }

      # Expose metrics endpoint for Prometheus
      startup_probe {
        http_get {
          path = "/health"
          port = 8000
        }
        initial_delay_seconds = 30
        timeout_seconds       = 5
        period_seconds        = 10  # check every 10 seconds
        failure_threshold     = 30  # 30 * 10s = 5 minutes before container is killed
      }

      liveness_probe {
        http_get {
          path = "/health"
          port = 8000
        }
        initial_delay_seconds = 300
        timeout_seconds       = 5
        period_seconds        = 10
        failure_threshold     = 6  # 60s of failure allowed
      }

      env {
        name  = "PYTHONUNBUFFERED"
        value = "1"
      }
      env {
        name  = "NO_AUTH"
        value = var.no_auth
      }
      env {
        name  = "TRELLO_BOARD_ID"
        value = var.trello_board_id
      }

      # Secret environment variables from Secret Manager
      dynamic "env" {
        for_each = local.secrets
        content {
          name = env.value
          value_source {
            secret_key_ref {
              # secret  = data.google_secret_manager_secret.secrets[env.key].secret_id
              secret  = env.key
              version = "latest"
            }
          }
        }
      }
    }
  }

  depends_on = [
    google_secret_manager_secret_iam_member.secret_access,
    google_compute_subnetwork.subnet
  ]
}

# Public access
resource "google_cloud_run_v2_service_iam_member" "public_access" {
  name     = google_cloud_run_v2_service.service.name
  location = google_cloud_run_v2_service.service.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}
