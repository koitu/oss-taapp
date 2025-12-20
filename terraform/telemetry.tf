# Allow SSH access
resource "google_compute_firewall" "allow_ssh" {
  name    = "allow-ssh"
  network = google_compute_network.vpc.name

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["monitoring"]
}

# Allow public access to Prometheus
resource "google_compute_firewall" "allow_prometheus_external" {
  name    = "allow-prometheus-external"
  network = google_compute_network.vpc.name

  allow {
    protocol = "tcp"
    ports    = ["9090"]
  }

  source_ranges = ["0.0.0.0/0"]  # Open to the world
  target_tags   = ["prometheus"]
}

# Allow public access to Grafana
resource "google_compute_firewall" "allow_grafana_external" {
  name    = "allow-grafana-external"
  network = google_compute_network.vpc.name

  allow {
    protocol = "tcp"
    ports    = ["3000"]
  }

  source_ranges = ["0.0.0.0/0"]  # Open to the world
  target_tags   = ["grafana"]
}

# Prometheus instance
resource "google_compute_instance" "prometheus" {
  name         = "prometheus-server"
  machine_type = "e2-small"
  zone         = "${var.region}-a"

  tags = ["monitoring", "prometheus"]

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-11"
      size  = 20
    }
  }

  network_interface {
    network    = google_compute_network.vpc.id
    subnetwork = google_compute_subnetwork.subnet.id

    access_config {
      # Ephemeral public IP
    }
  }

  metadata_startup_script = <<-EOF
    #!/bin/bash
    set -e

    # Log everything
    exec > >(tee /var/log/startup-script.log)
    exec 2>&1

    echo "Starting Prometheus installation..."

    apt-get update
    apt-get install -y wget

    cd /opt

    # Install Prometheus
    wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz
    tar xvfz prometheus-2.45.0.linux-amd64.tar.gz
    cd prometheus-2.45.0.linux-amd64

    # Create prometheus config
    cat > prometheus.yml <<EOL
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'ospsd-service'
    static_configs:
      - targets: ['${replace(replace(google_cloud_run_v2_service.service.uri, "https://", ""), ":443", "")}']
    metrics_path: '/metrics'
    scheme: 'https'
EOL

    # Create systemd service
    cat > /etc/systemd/system/prometheus.service <<EOL
[Unit]
Description=Prometheus
Wants=network-online.target
After=network-online.target

[Service]
User=root
ExecStart=/opt/prometheus-2.45.0.linux-amd64/prometheus --config.file=/opt/prometheus-2.45.0.linux-amd64/prometheus.yml --web.listen-address=:9090
Restart=always

[Install]
WantedBy=multi-user.target
EOL

    # Start Prometheus as a service
    systemctl daemon-reload
    systemctl start prometheus
    systemctl enable prometheus

    echo "Prometheus installation complete!"
  EOF

  service_account {
    email  = google_service_account.cloudrun.email
    scopes = ["cloud-platform"]
  }
}

# Grafana instance
resource "google_compute_instance" "grafana" {
  name         = "grafana-server"
  machine_type = "e2-small"
  zone         = "${var.region}-a"

  tags = ["monitoring", "grafana"]

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-11"
      size  = 20
    }
  }

  network_interface {
    network    = google_compute_network.vpc.id
    subnetwork = google_compute_subnetwork.subnet.id

    access_config {
      # Ephemeral public IP
    }
  }

  metadata_startup_script = <<-EOF
    #!/bin/bash
    set -e

    # Log everything
    exec > >(tee /var/log/startup-script.log)
    exec 2>&1

    echo "Starting Grafana installation..."

    apt-get update
    apt-get install -y apt-transport-https software-properties-common wget gnupg

    # Install Grafana
    mkdir -p /etc/apt/keyrings/
    wget -q -O - https://apt.grafana.com/gpg.key | gpg --dearmor | tee /etc/apt/keyrings/grafana.gpg > /dev/null
    echo "deb [signed-by=/etc/apt/keyrings/grafana.gpg] https://apt.grafana.com stable main" | tee /etc/apt/sources.list.d/grafana.list

    apt-get update
    apt-get install -y grafana

    # Configure Grafana to listen on all interfaces
    cat > /etc/grafana/grafana.ini <<EOL
[server]
http_addr = 0.0.0.0
http_port = 3000

[security]
admin_user = admin
admin_password = admin
EOL

    # Start Grafana
    systemctl daemon-reload
    systemctl start grafana-server
    systemctl enable grafana-server

    echo "Grafana installation complete!"
  EOF

  service_account {
    email  = google_service_account.cloudrun.email
    scopes = ["cloud-platform"]
  }
}
