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
  network       = "default"
  ip_cidr_range = "10.8.0.0/28"
}

# # Firewall rules for Prometheus scraping
# resource "google_compute_firewall" "allow_prometheus" {
#   name    = "allow-prometheus-scraping"
#   network = google_compute_network.vpc.name
#
#   allow {
#     protocol = "tcp"
#     ports    = ["9090", "3000", "8000"]  # Prometheus, Grafana, App
#   }
#
#   source_ranges = ["10.0.0.0/24"]
#   target_tags   = ["monitoring"]
# }

# Artifact Registry
resource "google_artifact_registry_repository" "repo" {
  provider    = google
  project     = var.project
  location    = var.region
  repository_id = var.artifact_repo
  description = "Docker repository for ospsd-service"
  format      = "DOCKER"

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

      # # Expose metrics endpoint for Prometheus
      # startup_probe {
      #   http_get {
      #     path = "/health"
      #     port = 8000
      #   }
      #   initial_delay_seconds = 0
      #   timeout_seconds       = 1
      #   period_seconds        = 3
      #   failure_threshold     = 1
      # }
      #
      # liveness_probe {
      #   http_get {
      #     path = "/health"
      #     port = 8000
      #   }
      #   initial_delay_seconds = 30
      #   timeout_seconds       = 1
      #   period_seconds        = 10
      #   failure_threshold     = 3
      # }

      env {
        name  = "PYTHONUNBUFFERED"
        value = "1"
      }
      env {
        name  = "TELEMETRY_EXPORT_PATH"
        value = var.telemetry_export_path
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


# # GCE Instance for Prometheus
# resource "google_compute_instance" "prometheus" {
#   name         = "prometheus-server"
#   machine_type = "e2-small"
#   zone         = "${var.region}-a"
#
#   tags = ["monitoring", "prometheus"]
#
#   boot_disk {
#     initialize_params {
#       image = "debian-cloud/debian-11"
#       size  = 20
#     }
#   }
#
#   network_interface {
#     network    = google_compute_network.vpc.id
#     subnetwork = google_compute_subnetwork.subnet.id
#
#     access_config {
#       # Ephemeral public IP for SSH access
#     }
#   }
#
#   metadata_startup_script = <<-EOF
#     #!/bin/bash
#     apt-get update
#     apt-get install -y wget
#
#     # Install Prometheus
#     wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz
#     tar xvfz prometheus-*.tar.gz
#     cd prometheus-*
#
#     # Create prometheus config
#     cat > prometheus.yml <<EOL
#     global:
#       scrape_interval: 15s
#
#     scrape_configs:
#       - job_name: 'ospsd-service'
#         static_configs:
#           - targets: ['${google_cloud_run_v2_service.service.uri}']
#         metrics_path: '/metrics'
#         scheme: 'https'
#     EOL
#
#     # Start Prometheus
#     nohup ./prometheus --config.file=prometheus.yml &
#   EOF
#
#   service_account {
#     email  = google_service_account.cloudrun.email
#     scopes = ["cloud-platform"]
#   }
# }
#
# # GCE Instance for Grafana
# resource "google_compute_instance" "grafana" {
#   name         = "grafana-server"
#   machine_type = "e2-small"
#   zone         = "${var.region}-a"
#
#   tags = ["monitoring", "grafana"]
#
#   boot_disk {
#     initialize_params {
#       image = "debian-cloud/debian-11"
#       size  = 20
#     }
#   }
#
#   network_interface {
#     network    = google_compute_network.vpc.id
#     subnetwork = google_compute_subnetwork.subnet.id
#
#     access_config {
#       # Ephemeral public IP
#     }
#   }
#
#   metadata_startup_script = <<-EOF
#     #!/bin/bash
#     apt-get update
#     apt-get install -y apt-transport-https software-properties-common wget
#
#     # Install Grafana
#     wget -q -O - https://packages.grafana.com/gpg.key | apt-key add -
#     echo "deb https://packages.grafana.com/oss/deb stable main" | tee /etc/apt/sources.list.d/grafana.list
#     apt-get update
#     apt-get install -y grafana
#
#     # Start Grafana
#     systemctl daemon-reload
#     systemctl start grafana-server
#     systemctl enable grafana-server
#   EOF
#
#   service_account {
#     email  = google_service_account.cloudrun.email
#     scopes = ["cloud-platform"]
#   }
# }
