output "raw_bucket" { value = aws_s3_bucket.raw.bucket }
output "vector_bucket_name" { value = aws_s3vectors_vector_bucket.vectors.vector_bucket_name }
output "vector_index_name" { value = aws_s3vectors_index.chunks.index_name }
output "chunks_table" { value = aws_dynamodb_table.chunks.name }
output "terms_table" { value = aws_dynamodb_table.terms.name }
output "docstats_table" { value = aws_dynamodb_table.docstats.name }
output "cache_table" { value = aws_dynamodb_table.cache.name }
output "evallog_table" { value = aws_dynamodb_table.evallog.name }
output "raw_bucket_arn" { value = aws_s3_bucket.raw.arn }
output "vector_index_arn" { value = aws_s3vectors_index.chunks.index_arn }
output "table_arns" {
  value = [
    aws_dynamodb_table.chunks.arn,
    aws_dynamodb_table.terms.arn,
    aws_dynamodb_table.docstats.arn,
  ]
}
output "cache_table_arn" { value = aws_dynamodb_table.cache.arn }
