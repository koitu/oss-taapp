# Deploy to Cloud Run (Terraform)

Prereqs:
- Install and authenticate `gcloud` and `terraform`.
- Enable the GCP project you will use and set it as active: `gcloud config set project YOUR_PROJECT`

Steps:

1) Configure variables

- Edit `terraform/gcp/terraform.tfvars` or pass `-var` flags. Example `terraform.tfvars`:

```
project = "my-gcp-project"
region  = "us-central1"
image   = "us-central1-docker.pkg.dev/my-gcp-project/oss-repo/ospsd-service:latest"
```

2) Build and push the container image to Artifact Registry

Replace `us-central1` and `my-gcp-project` with your values.

```
# Authenticate Docker to Artifact Registry
gcloud auth configure-docker ${REGION}-docker.pkg.dev

# Build
docker build -t ${REGION}-docker.pkg.dev/${PROJECT}/${REPO}/ospsd-service:latest .

# Push
docker push ${REGION}-docker.pkg.dev/${PROJECT}/${REPO}/ospsd-service:latest
```

3) Initialize and apply Terraform

```
cd terraform/gcp
terraform init
terraform apply -var="project=MY_PROJECT" -var="region=us-central1" -var="image=us-central1-docker.pkg.dev/MY_PROJECT/oss-repo/ospsd-service:latest"
```

Notes & next steps:
- The Cloud Run service created by Terraform is public (invoker = allUsers). For a private service, remove the `google_cloud_run_service_iam_member` resource or replace with suitable IAM.
- This config provisions Artifact Registry, a serverless VPC connector (for future Cloud SQL connectivity), a service account and a Cloud Run service. It does NOT migrate local SQLite files to a managed database. For persistent data, migrate to Cloud SQL or another managed DB and update the application to use it.
- If you'd like Terraform to trigger an automated build (Cloud Build), we can add a `google_cloudbuild_trigger` that builds on git push or upload the source to GCS and create a `google_cloudbuild_build` resource.
