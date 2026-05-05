# marsie report bucket — Terraform

Provisions a private, versioned, encrypted S3 bucket plus a dedicated IAM user
(with an inline policy scoped to that bucket) for the Lab-Admin report
uploader.

## Prerequisites

- `terraform` ≥ 1.6
- `aws` CLI configured with credentials for the marsie account
  (`760370882375`, IAM user `Miguel_segura_student`).

The provider does not pin a profile; it uses your default credential chain.
**Verify the right account before applying:**

```bash
aws sts get-caller-identity
# Account must be 760370882375. Abort if anything else.
```

## Quick start

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars
# edit terraform.tfvars: set a globally-unique bucket_name (e.g. marsie-reports-msegura-dev)

terraform init
terraform plan
terraform apply
```

Capture the outputs into your repo's `.env`:

```bash
echo "AWS_S3_BUCKET=$(terraform output -raw bucket_name)"            >> ../../.env
echo "AWS_S3_REGION=$(terraform output -raw bucket_region)"          >> ../../.env
echo "AWS_ACCESS_KEY_ID=$(terraform output -raw access_key_id)"      >> ../../.env
echo "AWS_SECRET_ACCESS_KEY=$(terraform output -raw secret_access_key)" >> ../../.env
```

(Or copy by hand — they're all marked sensitive.)

## Tear-down

```bash
# Bucket must be empty first
aws s3 rm "s3://$(terraform output -raw bucket_name)" --recursive
terraform destroy
```

## Notes

- State is local. When more than one developer works on infra, migrate to a
  remote backend (S3 + DynamoDB lock) — five-line change in `versions.tf`.
- The IAM user is dev-only. Production should run under an attached IAM role,
  not a long-lived access key.
