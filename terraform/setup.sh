#!/bin/bash

# Minimal GCS Backend Setup Script
# Creates bucket and configures backend without versioning/backup

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         Minimal Terraform GCS Backend Setup               ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Configuration
PROJECT_ID="${TF_VAR_project:-your-project-id}"
REGION="${TF_VAR_region:-us-central1}"
BUCKET_NAME="ospsd-terraform-state"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --project)
            PROJECT_ID="$2"
            shift 2
            ;;
        --region)
            REGION="$2"
            shift 2
            ;;
        --bucket)
            BUCKET_NAME="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --project PROJECT_ID   GCP Project ID"
            echo "  --region REGION        GCP Region"
            echo "  --bucket BUCKET_NAME   State bucket name (must be globally unique)"
            echo "  --help, -h             Show this help"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

echo "Configuration:"
echo "  Project:      $PROJECT_ID"
echo "  Region:       $REGION"
echo "  State Bucket: $BUCKET_NAME"
echo ""

# Check prerequisites
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI not found${NC}"
    exit 1
fi

if ! command -v terraform &> /dev/null; then
    echo -e "${RED}Error: terraform not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites OK${NC}\n"

# Check if bucket exists
echo -e "${YELLOW}Checking if bucket exists...${NC}"
if gsutil ls -b gs://$BUCKET_NAME &> /dev/null; then
    echo -e "${YELLOW}Bucket already exists, skipping creation${NC}"
else
    echo -e "${YELLOW}Creating bucket: $BUCKET_NAME${NC}"
    gsutil mb -p $PROJECT_ID -c STANDARD -l $REGION gs://$BUCKET_NAME
    gsutil ubla set on gs://$BUCKET_NAME
    echo -e "${GREEN}✓ Bucket created${NC}"
fi

echo ""

# Create backend configuration
echo -e "${YELLOW}Creating backend.tf...${NC}"
cat > backend.tf <<EOF
# backend.tf
terraform {
  backend "gcs" {
    bucket  = "$BUCKET_NAME"
    prefix  = "terraform/state"
  }
}
EOF

echo -e "${GREEN}✓ Created backend.tf${NC}\n"

# Initialize backend
echo -e "${YELLOW}Initializing Terraform backend...${NC}"
if [ -f "terraform.tfstate" ]; then
    echo -e "${YELLOW}Migrating existing state to GCS...${NC}"
    terraform init -migrate-state
else
    terraform init
fi

echo -e "${GREEN}✓ Backend initialized${NC}\n"

# Verify
echo -e "${YELLOW}Verifying state in GCS...${NC}"
if gsutil ls gs://$BUCKET_NAME/terraform/state/ &> /dev/null; then
    echo -e "${GREEN}✓ State successfully stored in GCS${NC}"
else
    echo -e "${RED}Warning: State not found in bucket${NC}"
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "State Location: gs://$BUCKET_NAME/terraform/state/"
echo ""
echo "Next steps:"
echo "  1. Run 'terraform plan' to verify"
echo "  2. Team members should run 'terraform init'"
echo ""
