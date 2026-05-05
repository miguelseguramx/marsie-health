output "bucket_name" {
  description = "S3 bucket holding raw report PDFs."
  value       = aws_s3_bucket.reports.bucket
}

output "bucket_region" {
  description = "Region the bucket lives in."
  value       = var.aws_region
}

output "access_key_id" {
  description = "Access key ID for the uploader IAM user."
  value       = aws_iam_access_key.uploader.id
  sensitive   = true
}

output "secret_access_key" {
  description = "Secret access key for the uploader IAM user. Retrieve with `terraform output -raw secret_access_key`."
  value       = aws_iam_access_key.uploader.secret
  sensitive   = true
}
