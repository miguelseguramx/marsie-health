variable "aws_region" {
  description = "AWS region for the report bucket and IAM resources."
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment label used in resource names (e.g. dev, staging, prod)."
  type        = string
}

variable "bucket_name" {
  description = "Globally unique S3 bucket name for raw report PDFs."
  type        = string
}
