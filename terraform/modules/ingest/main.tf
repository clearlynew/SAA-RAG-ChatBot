data "aws_caller_identity" "me" {}

# ---------- queues ----------
resource "aws_sqs_queue" "dlq" {
  name                      = "${var.project}-ingest-dlq"
  message_retention_seconds = 1209600 # 14 days
}

resource "aws_sqs_queue" "ingest" {
  name                       = "${var.project}-ingest"
  visibility_timeout_seconds = 1800 # 6x the Lambda timeout
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 3
  })
}

# Let our raw bucket (and only it) send messages to the queue
resource "aws_sqs_queue_policy" "allow_s3" {
  queue_url = aws_sqs_queue.ingest.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "s3.amazonaws.com" }
      Action    = "sqs:SendMessage"
      Resource  = aws_sqs_queue.ingest.arn
      Condition = {
        ArnEquals    = { "aws:SourceArn" = var.raw_bucket_arn }
        StringEquals = { "aws:SourceAccount" = data.aws_caller_identity.me.account_id }
      }
    }]
  })
}

# New .md file in the bucket -> message in the queue
resource "aws_s3_bucket_notification" "raw" {
  bucket = var.raw_bucket_name
  queue {
    queue_arn     = aws_sqs_queue.ingest.arn
    events        = ["s3:ObjectCreated:*"]
    filter_suffix = ".md"
  }
  depends_on = [aws_sqs_queue_policy.allow_s3]
}

# ---------- logs ----------
resource "aws_cloudwatch_log_group" "ingest" {
  name              = "/aws/lambda/${var.project}-ingest"
  retention_in_days = 14
}

# ---------- permissions ----------
resource "aws_iam_role" "ingest" {
  name = "${var.project}-ingest-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "ingest" {
  name = "ingest-permissions"
  role = aws_iam_role.ingest.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "Logs"
        Effect   = "Allow"
        Action   = ["logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "${aws_cloudwatch_log_group.ingest.arn}:*"
      },
      {
        Sid      = "Queue"
        Effect   = "Allow"
        Action   = ["sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes"]
        Resource = aws_sqs_queue.ingest.arn
      },
      {
        Sid      = "ReadDocs"
        Effect   = "Allow"
        Action   = "s3:GetObject"
        Resource = "${var.raw_bucket_arn}/*"
      },
      {
        Sid      = "WriteTables"
        Effect   = "Allow"
        Action   = ["dynamodb:PutItem", "dynamodb:BatchWriteItem"]
        Resource = var.table_arns
      },
      {
        Sid      = "WriteVectors"
        Effect   = "Allow"
        Action   = "s3vectors:PutVectors"
        Resource = var.vector_index_arn
      },
      {
        Sid      = "Embed"
        Effect   = "Allow"
        Action   = "bedrock:InvokeModel"
        Resource = "arn:aws:bedrock:${var.region}::foundation-model/amazon.titan-embed-text-v2:0"
      },
    ]
  })
}

# ---------- the function ----------
data "archive_file" "ingest" {
  type        = "zip"
  source_dir  = "${path.root}/../lambdas/ingest"
  output_path = "${path.module}/ingest.zip"
  excludes    = ["__pycache__", ".pytest_cache", "test_*.py", "run_local.py"]
}

resource "aws_lambda_function" "ingest" {
  function_name    = "${var.project}-ingest"
  role             = aws_iam_role.ingest.arn
  runtime          = "python3.12"
  handler          = "handler.handler" # file handler.py, function handler
  filename         = data.archive_file.ingest.output_path
  source_code_hash = data.archive_file.ingest.output_base64sha256
  timeout          = 300
  memory_size      = 512

  environment {
    variables = {
      VECTOR_BUCKET  = var.vector_bucket_name
      VECTOR_INDEX   = var.vector_index_name
      CHUNKS_TABLE   = var.chunks_table
      TERMS_TABLE    = var.terms_table
      DOCSTATS_TABLE = var.docstats_table
    }
  }

  depends_on = [aws_cloudwatch_log_group.ingest, aws_iam_role_policy.ingest]
}

# Queue -> Lambda
resource "aws_lambda_event_source_mapping" "ingest" {
  event_source_arn = aws_sqs_queue.ingest.arn
  function_name    = aws_lambda_function.ingest.arn
  batch_size       = 1

  scaling_config {
    maximum_concurrency = 2
  }
}
