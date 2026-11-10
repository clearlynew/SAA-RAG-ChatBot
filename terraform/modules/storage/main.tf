data "aws_caller_identity" "me" {}

locals {
  suffix = data.aws_caller_identity.me.account_id
}

# --- Raw whitepapers (input to ingest) ---
resource "aws_s3_bucket" "raw" {
  bucket        = "${var.project}-raw-${local.suffix}"
  force_destroy = true
}

resource "aws_s3_bucket_public_access_block" "raw" {
  bucket                  = aws_s3_bucket.raw.id
  block_public_acls       = true
  ignore_public_acls      = true
  block_public_policy     = true
  restrict_public_buckets = true
}

# --- Vector store ---
resource "aws_s3vectors_vector_bucket" "vectors" {
  vector_bucket_name = "${var.project}-vectors-${local.suffix}"
  force_destroy      = true
}

resource "aws_s3vectors_index" "chunks" {
  index_name         = "chunks"
  vector_bucket_name = aws_s3vectors_vector_bucket.vectors.vector_bucket_name
  data_type          = "float32"
  dimension          = 1024 # must match Titan Embeddings V2 output
  distance_metric    = "cosine"
}

# --- DynamoDB tables ---
resource "aws_dynamodb_table" "chunks" {
  name         = "${var.project}-chunks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "chunk_id"
  attribute {
    name = "chunk_id"
    type = "S"
  }
}

resource "aws_dynamodb_table" "terms" {
  name         = "${var.project}-terms"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "term"
  range_key    = "chunk_id"
  attribute {
    name = "term"
    type = "S"
  }
  attribute {
    name = "chunk_id"
    type = "S"
  }
}

resource "aws_dynamodb_table" "docstats" {
  name         = "${var.project}-docstats"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "chunk_id"
  attribute {
    name = "chunk_id"
    type = "S"
  }
}

resource "aws_dynamodb_table" "cache" {
  name         = "${var.project}-cache"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "query_hash"
  attribute {
    name = "query_hash"
    type = "S"
  }
  ttl {
    attribute_name = "ttl"
    enabled        = true
  }
}

resource "aws_dynamodb_table" "evallog" {
  name         = "${var.project}-evallog"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "run_id"
  range_key    = "question_id"
  attribute {
    name = "run_id"
    type = "S"
  }
  attribute {
    name = "question_id"
    type = "S"
  }
}
