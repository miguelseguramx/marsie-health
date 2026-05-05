resource "aws_s3_bucket" "reports" {
  bucket = var.bucket_name

  tags = {
    Project     = "marsie"
    Environment = var.environment
    Purpose     = "raw-report-pdfs"
  }
}

resource "aws_s3_bucket_ownership_controls" "reports" {
  bucket = aws_s3_bucket.reports.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_public_access_block" "reports" {
  bucket = aws_s3_bucket.reports.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "reports" {
  bucket = aws_s3_bucket.reports.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "reports" {
  bucket = aws_s3_bucket.reports.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_iam_user" "uploader" {
  name = "marsie-reports-uploader-${var.environment}"

  tags = {
    Project     = "marsie"
    Environment = var.environment
  }
}

resource "aws_iam_user_policy" "uploader" {
  name = "marsie-reports-uploader-${var.environment}"
  user = aws_iam_user.uploader.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ObjectRW"
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:DeleteObject",
        ]
        Resource = "${aws_s3_bucket.reports.arn}/*"
      },
      {
        Sid    = "ListBucket"
        Effect = "Allow"
        Action = [
          "s3:ListBucket",
        ]
        Resource = aws_s3_bucket.reports.arn
      },
    ]
  })
}

resource "aws_iam_access_key" "uploader" {
  user = aws_iam_user.uploader.name
}
