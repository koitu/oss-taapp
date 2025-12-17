#!/bin/bash
PROJECT="ospsd-471816"
REGION="us-central1"  # Adjust as needed
REPO_NAME="ospsd-repo"  # Adjust as needed

# TODO: is there some way to import all?

# Import repository
terraform import google_artifact_registry_repository.repo \
  projects/$PROJECT/locations/$REGION/repositories/$REPO_NAME

# Import service account
terraform import google_service_account.cloudrun \
  projects/$PROJECT/serviceAccounts/ospsd-cloudrun-sa@$PROJECT.iam.gserviceaccount.com

# Import Cloud Run service
terraform import google_cloud_run_v2_service.service \
  projects/$PROJECT/locations/$REGION/services/ospsd-service

echo "Import complete. Run 'terraform plan' to verify."
