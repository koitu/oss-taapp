resource "google_project_service" "required_apis" {
  for_each = toset([
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "iam.googleapis.com",
    "vpcaccess.googleapis.com"
  ])
  service = each.key
}

resource "google_artifact_registry_repository" "repo" {
  provider    = google
  project     = var.project
  location    = var.region
  repository_id = var.artifact_repo
  description = "Docker repository for ospsd-service"
  format      = "DOCKER"
}

resource "google_service_account" "cloudrun" {
  account_id   = "ospsd-cloudrun-sa"
  display_name = "Service account for Cloud Run ospsd-service"
}

resource "google_project_iam_member" "cloudrun_cloudbuild_roles" {
  project = var.project
  role    = "roles/run.admin"
  member  = "serviceAccount:${google_service_account.cloudrun.email}"
}

resource "google_vpc_access_connector" "serverless_connector" {
  name          = "ospsd-connector"
  region        = var.region
  project       = var.project
  network       = "default"
  ip_cidr_range = "10.8.0.0/28"
}

resource "google_cloud_run_service" "service" {
  name     = var.service_name
  location = var.region

  metadata {
    annotations = {
      "run.googleapis.com/ingress" = "all"
    }
  }

  template {
    metadata {
      annotations = {
        "run.googleapis.com/vpc-access-connector" = google_vpc_access_connector.serverless_connector.name
      }
    }

    spec {
      service_account_name = google_service_account.cloudrun.email
      timeout_seconds = 300

      containers {
        image = var.image

        env {
          name  = "PYTHONUNBUFFERED"
          value = "1"
        }
        env {
          name  = "TELEMETRY_EXPORT_PATH"
          value = var.telemetry_export_path
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}

resource "google_cloud_run_service_iam_member" "editor_user" {
  service = google_cloud_run_service.service.name
  location = var.region
  role    = "roles/editor"
  member  = "allUsers"
}
