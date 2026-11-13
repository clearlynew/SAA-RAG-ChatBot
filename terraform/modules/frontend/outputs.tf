output "domain" { value = aws_cloudfront_distribution.site.domain_name }
output "bucket" { value = aws_s3_bucket.site.bucket }
