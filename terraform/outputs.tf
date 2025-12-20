output "cloud_run_url" {
  description = "The URL of the deployed Cloud Run service"
  value       = google_cloud_run_v2_service.service.uri
}

output "artifact_repo" {
  description = "Artifact Registry repository path"
  value       = "${var.region}-docker.pkg.dev/${var.project}/${var.artifact_repo}"
}

output "prometheus_ip" {
  description = "Prometheus server external IP"
  value       = google_compute_instance.prometheus.network_interface[0].access_config[0].nat_ip
}

output "prometheus_url" {
  description = "Prometheus dashboard URL"
  value       = "http://${google_compute_instance.prometheus.network_interface[0].access_config[0].nat_ip}:9090"
}

output "grafana_ip" {
  description = "Grafana server external IP"
  value       = google_compute_instance.grafana.network_interface[0].access_config[0].nat_ip
}

output "grafana_url" {
  description = "Grafana dashboard URL"
  value       = "http://${google_compute_instance.grafana.network_interface[0].access_config[0].nat_ip}:3000"
}
