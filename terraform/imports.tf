# Import existing project services
import {
  to = google_project_service.required_apis["run.googleapis.com"]
  id = "${var.project}/run.googleapis.com"
}

import {
  to = google_project_service.required_apis["artifactregistry.googleapis.com"]
  id = "${var.project}/artifactregistry.googleapis.com"
}

import {
  to = google_project_service.required_apis["cloudbuild.googleapis.com"]
  id = "${var.project}/cloudbuild.googleapis.com"
}

import {
  to = google_project_service.required_apis["iam.googleapis.com"]
  id = "${var.project}/iam.googleapis.com"
}

import {
  to = google_project_service.required_apis["secretmanager.googleapis.com"]
  id = "${var.project}/secretmanager.googleapis.com"
}

import {
  to = google_project_service.required_apis["compute.googleapis.com"]
  id = "${var.project}/compute.googleapis.com"
}

import {
  to = google_project_service.required_apis["vpcaccess.googleapis.com"]
  id = "${var.project}/vpcaccess.googleapis.com"
}

# Import VPC Network
import {
  to = google_compute_network.vpc
  id = "projects/${var.project}/global/networks/ospsd-vpc"
}

# Import Subnet
import {
  to = google_compute_subnetwork.subnet
  id = "projects/${var.project}/regions/${var.region}/subnetworks/ospsd-subnet"
}

# Import VPC Access Connector
import {
  to = google_vpc_access_connector.serverless_connector
  id = "projects/${var.project}/locations/${var.region}/connectors/ospsd-connector"
}

# # Import Firewall Rule
# import {
#   to = google_compute_firewall.allow_prometheus
#   id = "projects/${var.project}/global/firewalls/allow-prometheus-scraping"
# }

# Import Artifact Registry Repository
import {
  to = google_artifact_registry_repository.repo
  id = "projects/${var.project}/locations/${var.region}/repositories/${var.artifact_repo}"
}

# Import Service Account
import {
  to = google_service_account.cloudrun
  id = "projects/${var.project}/serviceAccounts/ospsd-cloudrun-sa@${var.project}.iam.gserviceaccount.com"
}

# Import IAM Policy Binding
import {
  to = google_project_iam_member.cloudrun_cloudbuild_roles
  id = "${var.project} roles/run.admin serviceAccount:ospsd-cloudrun-sa@${var.project}.iam.gserviceaccount.com"
}

# Import Secret Manager IAM Members
import {
  to = google_secret_manager_secret_iam_member.secret_access["DISCORD_CLIENT_ID"]
  id = "projects/${var.project}/secrets/DISCORD_CLIENT_ID roles/secretmanager.secretAccessor serviceAccount:ospsd-cloudrun-sa@${var.project}.iam.gserviceaccount.com"
}

import {
  to = google_secret_manager_secret_iam_member.secret_access["DISCORD_CLIENT_SECRET"]
  id = "projects/${var.project}/secrets/DISCORD_CLIENT_SECRET roles/secretmanager.secretAccessor serviceAccount:ospsd-cloudrun-sa@${var.project}.iam.gserviceaccount.com"
}

import {
  to = google_secret_manager_secret_iam_member.secret_access["DISCORD_PUBLIC_KEY"]
  id = "projects/${var.project}/secrets/DISCORD_PUBLIC_KEY roles/secretmanager.secretAccessor serviceAccount:ospsd-cloudrun-sa@${var.project}.iam.gserviceaccount.com"
}

import {
  to = google_secret_manager_secret_iam_member.secret_access["DISCORD_BOT_TOKEN"]
  id = "projects/${var.project}/secrets/DISCORD_BOT_TOKEN roles/secretmanager.secretAccessor serviceAccount:ospsd-cloudrun-sa@${var.project}.iam.gserviceaccount.com"
}

import {
  to = google_secret_manager_secret_iam_member.secret_access["OPENAI_API_KEY"]
  id = "projects/${var.project}/secrets/OPENAI_API_KEY roles/secretmanager.secretAccessor serviceAccount:ospsd-cloudrun-sa@${var.project}.iam.gserviceaccount.com"
}

import {
  to = google_secret_manager_secret_iam_member.secret_access["CLAUDE_API_KEY"]
  id = "projects/${var.project}/secrets/CLAUDE_API_KEY roles/secretmanager.secretAccessor serviceAccount:ospsd-cloudrun-sa@${var.project}.iam.gserviceaccount.com"
}

import {
  to = google_secret_manager_secret_iam_member.secret_access["TRELLO_API_KEY"]
  id = "projects/${var.project}/secrets/TRELLO_API_KEY roles/secretmanager.secretAccessor serviceAccount:ospsd-cloudrun-sa@${var.project}.iam.gserviceaccount.com"
}

import {
  to = google_secret_manager_secret_iam_member.secret_access["TRELLO_API_SECRET"]
  id = "projects/${var.project}/secrets/TRELLO_API_SECRET roles/secretmanager.secretAccessor serviceAccount:ospsd-cloudrun-sa@${var.project}.iam.gserviceaccount.com"
}

# Import Cloud Run Service
import {
  to = google_cloud_run_v2_service.service
  id = "projects/${var.project}/locations/${var.region}/services/${var.service_name}"
}

# Import Cloud Run IAM Member
import {
  to = google_cloud_run_v2_service_iam_member.public_access
  id = "projects/${var.project}/locations/${var.region}/services/${var.service_name} roles/run.invoker allUsers"
}

# # Import Prometheus GCE Instance
# import {
#   to = google_compute_instance.prometheus
#   id = "projects/${var.project}/zones/${var.region}-a/instances/prometheus-server"
# }
#
# # Import Grafana GCE Instance
# import {
#   to = google_compute_instance.grafana
#   id = "projects/${var.project}/zones/${var.region}-a/instances/grafana-server"
# }