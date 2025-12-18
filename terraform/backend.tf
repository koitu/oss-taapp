# store the terraform.tfstate in a gcp bucket
terraform {
  backend "gcs" {
    bucket  = "ospsd-terraform-state"
    prefix  = "terraform/state"
  }
}
