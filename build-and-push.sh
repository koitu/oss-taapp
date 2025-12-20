#!/bin/bash

# Configuration
PROJECT_ID="ospsd-471816"
REGION="us-central1"
REPO="ospsd-repo"
IMAGE_NAME="ospsd-service"
TAG="latest"  # Or use version tags like "v1.0.0"

# Full image path
IMAGE_PATH="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/${IMAGE_NAME}:${TAG}"

echo "Building Docker image..."
docker build -t ${IMAGE_PATH} .

echo "Configuring Docker authentication..."
gcloud auth configure-docker ${REGION}-docker.pkg.dev

echo "Pushing image to Artifact Registry..."
docker push ${IMAGE_PATH}

echo "✅ Image pushed successfully!"
echo "Image: ${IMAGE_PATH}"
echo ""
echo "Update your terraform.tfvars with:"
echo "image = \"${IMAGE_PATH}\""
