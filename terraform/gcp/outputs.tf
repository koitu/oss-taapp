output "cloud_run_url" {
  description = "The URL of the deployed Cloud Run service"
  value       = google_cloud_run_service.service.status[0].url
}

output "artifact_repo" {
  description = "Artifact Registry repository path"
  value       = "${var.region}-docker.pkg.dev/${var.project}/${var.artifact_repo}"
}
