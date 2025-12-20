#!/bin/bash

# Terraform Import Script
# This script (attempts) to import all existing GCP resources into Terraform state
# I forgot to upload the state on my other machine...

# now that terraform.tfstate is in a gcp bucket we don't really need this script anymore

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration - UPDATE THESE VALUES
PROJECT_ID="ospsd-471816"
REGION="us-central1"
SERVICE_NAME="ospsd-service"
ARTIFACT_REPO="ospsd-repo"
TRELLO_BOARD_ID="3pi4Wu6q"

echo -e "${YELLOW}=== Terraform Import Script ===${NC}"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Function to import resource with error handling
import_resource() {
    local resource_address=$1
    local resource_id=$2

    echo -e "${YELLOW}Importing: ${resource_address}${NC}"

    if terraform import "$resource_address" "$resource_id" 2>/dev/null; then
        echo -e "${GREEN}✓ Successfully imported: ${resource_address}${NC}"
    else
        echo -e "${RED}✗ Failed to import: ${resource_address}${NC}"
        echo -e "${RED}  Resource ID: ${resource_id}${NC}"
    fi
    echo ""
}

echo -e "${YELLOW}Starting imports...${NC}\n"

# 1. Project Services (APIs)
echo -e "${YELLOW}=== Importing Project Services ===${NC}"
import_resource 'google_project_service.required_apis["run.googleapis.com"]' "$PROJECT_ID/run.googleapis.com"
import_resource 'google_project_service.required_apis["artifactregistry.googleapis.com"]' "$PROJECT_ID/artifactregistry.googleapis.com"
import_resource 'google_project_service.required_apis["cloudbuild.googleapis.com"]' "$PROJECT_ID/cloudbuild.googleapis.com"
import_resource 'google_project_service.required_apis["iam.googleapis.com"]' "$PROJECT_ID/iam.googleapis.com"
import_resource 'google_project_service.required_apis["secretmanager.googleapis.com"]' "$PROJECT_ID/secretmanager.googleapis.com"
import_resource 'google_project_service.required_apis["compute.googleapis.com"]' "$PROJECT_ID/compute.googleapis.com"
import_resource 'google_project_service.required_apis["vpcaccess.googleapis.com"]' "$PROJECT_ID/vpcaccess.googleapis.com"

# 2. VPC Network
echo -e "${YELLOW}=== Importing VPC Network ===${NC}"
import_resource 'google_compute_network.vpc' "projects/$PROJECT_ID/global/networks/ospsd-vpc"

# 3. Subnet
echo -e "${YELLOW}=== Importing Subnet ===${NC}"
import_resource 'google_compute_subnetwork.subnet' "projects/$PROJECT_ID/regions/$REGION/subnetworks/ospsd-subnet"

# 4. VPC Access Connector
echo -e "${YELLOW}=== Importing VPC Access Connector ===${NC}"
import_resource 'google_vpc_access_connector.serverless_connector' "projects/$PROJECT_ID/locations/$REGION/connectors/ospsd-connector"

# 5. Artifact Registry
echo -e "${YELLOW}=== Importing Artifact Registry ===${NC}"
import_resource 'google_artifact_registry_repository.repo' "projects/$PROJECT_ID/locations/$REGION/repositories/$ARTIFACT_REPO"

# 6. Service Account
echo -e "${YELLOW}=== Importing Service Account ===${NC}"
import_resource 'google_service_account.cloudrun' "projects/$PROJECT_ID/serviceAccounts/ospsd-cloudrun-sa@$PROJECT_ID.iam.gserviceaccount.com"

# 7. IAM Member
echo -e "${YELLOW}=== Importing IAM Member ===${NC}"
import_resource 'google_project_iam_member.cloudrun_cloudbuild_roles' "$PROJECT_ID roles/run.admin serviceAccount:ospsd-cloudrun-sa@$PROJECT_ID.iam.gserviceaccount.com"

# 8. Secret Manager Secrets (data sources - no import needed)
echo -e "${YELLOW}=== Secret Manager Secrets (data sources - no import needed) ===${NC}"

# 9. Secret Manager IAM Members
echo -e "${YELLOW}=== Importing Secret Manager IAM Members ===${NC}"
SECRETS=("DISCORD_CLIENT_ID" "DISCORD_CLIENT_SECRET" "DISCORD_PUBLIC_KEY" "DISCORD_BOT_TOKEN" "OPENAI_API_KEY" "CLAUDE_API_KEY" "TRELLO_API_KEY" "TRELLO_API_SECRET")

for secret in "${SECRETS[@]}"; do
    import_resource "google_secret_manager_secret_iam_member.secret_access[\"$secret\"]" "projects/$PROJECT_ID/secrets/$secret roles/secretmanager.secretAccessor serviceAccount:ospsd-cloudrun-sa@$PROJECT_ID.iam.gserviceaccount.com"
done

# 10. Cloud Run Service
echo -e "${YELLOW}=== Importing Cloud Run Service ===${NC}"
import_resource 'google_cloud_run_v2_service.service' "projects/$PROJECT_ID/locations/$REGION/services/$SERVICE_NAME"

# 11. Cloud Run IAM Member (public access)
echo -e "${YELLOW}=== Importing Cloud Run IAM Member ===${NC}"
import_resource 'google_cloud_run_v2_service_iam_member.public_access' "projects/$PROJECT_ID/locations/$REGION/services/$SERVICE_NAME roles/run.invoker allUsers"

# 12. Firewall Rules
echo -e "${YELLOW}=== Importing Firewall Rules ===${NC}"
import_resource 'google_compute_firewall.allow_ssh' "projects/$PROJECT_ID/global/firewalls/allow-ssh"
import_resource 'google_compute_firewall.allow_prometheus_external' "projects/$PROJECT_ID/global/firewalls/allow-prometheus-external"
import_resource 'google_compute_firewall.allow_grafana_external' "projects/$PROJECT_ID/global/firewalls/allow-grafana-external"

# 13. Compute Instances
echo -e "${YELLOW}=== Importing Compute Instances ===${NC}"
import_resource 'google_compute_instance.prometheus' "projects/$PROJECT_ID/zones/$REGION-a/instances/prometheus-server"
import_resource 'google_compute_instance.grafana' "projects/$PROJECT_ID/zones/$REGION-a/instances/grafana-server"

echo -e "${GREEN}=== Import process complete! ===${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Review the import results above"
echo "2. Run 'terraform plan' to see if there are any differences"
echo "3. Update your terraform.tfvars file with the correct values"
echo "4. Address any remaining differences in the plan"
