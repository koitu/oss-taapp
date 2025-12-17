project                = "ospsd-471816"
region                 = "us-central1"
service_name           = "ospsd-service"
artifact_repo          = "ospsd-repo"
image                  = "us-central1-docker.pkg.dev/ospsd-471816/ospsd-repo/ospsd-service:latest"

# Non-secret config
telemetry_export_path  = "telemetry/metrics.json"
no_auth                = "true"
trello_board_id        = "3pi4Wu6q"