data "aws_caller_identity" "me" {}

resource "aws_cloudwatch_log_group" "query" {
  name              = "/aws/lambda/${var.project}-query"
  retention_in_days = 14
}

resource "aws_iam_role" "query" {
  name = "${var.project}-query-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "query" {
  name = "query-permissions"
  role = aws_iam_role.query.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "Logs"
        Effect   = "Allow"
        Action   = ["logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "${aws_cloudwatch_log_group.query.arn}:*"
      },
      {
        Sid      = "ReadSearchTables"
        Effect   = "Allow"
        Action   = ["dynamodb:GetItem", "dynamodb:BatchGetItem", "dynamodb:Query", "dynamodb:Scan"]
        Resource = var.table_arns
      },
      {
        Sid      = "Cache"
        Effect   = "Allow"
        Action   = ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:UpdateItem"]
        Resource = var.cache_table_arn
      },
      {
        Sid      = "VectorSearch"
        Effect   = "Allow"
        Action   = "s3vectors:QueryVectors"
        Resource = var.vector_index_arn
      },
      {
        Sid    = "Models"
        Effect = "Allow"
        Action = "bedrock:InvokeModel"
        Resource = [
          "arn:aws:bedrock:${var.region}::foundation-model/amazon.titan-embed-text-v2:0",
          "arn:aws:bedrock:*::foundation-model/amazon.nova-lite-v1:0",
          "arn:aws:bedrock:${var.region}:${data.aws_caller_identity.me.account_id}:inference-profile/us.amazon.nova-lite-v1:0",
        ]
      },
    ]
  })
}

data "archive_file" "query" {
  type        = "zip"
  source_dir  = "${path.root}/../lambdas/query"
  output_path = "${path.module}/query.zip"
  excludes = [
    "__pycache__", ".pytest_cache", "ask.py", "search.py", "grounding.py",
    "test_rerank.py", "test_scoring.py", "test_generate.py",
    "test_keywords_sync.py", "test_validation.py",
  ]
}

resource "aws_lambda_function" "query" {
  function_name                  = "${var.project}-query"
  role                           = aws_iam_role.query.arn
  runtime                        = "python3.12"
  handler                        = "handler.handler"
  filename                       = data.archive_file.query.output_path
  source_code_hash               = data.archive_file.query.output_base64sha256
  timeout                        = 29 # API Gateway HTTP APIs cut off at 30 s
  memory_size                    = 1024
  reserved_concurrent_executions = var.reserved_concurrency

  environment {
    variables = {
      VECTOR_BUCKET   = var.vector_bucket_name
      VECTOR_INDEX    = var.vector_index_name
      CHUNKS_TABLE    = var.chunks_table
      TERMS_TABLE     = var.terms_table
      DOCSTATS_TABLE  = var.docstats_table
      CACHE_TABLE     = var.cache_table
      DAILY_LIMIT     = tostring(var.daily_limit)
      EMBED_MODEL_ID  = "amazon.titan-embed-text-v2:0"
      GEN_MODEL_ID    = "us.amazon.nova-lite-v1:0"
      RERANK_MODEL_ID = "us.amazon.nova-lite-v1:0"
    }
  }

  depends_on = [aws_cloudwatch_log_group.query, aws_iam_role_policy.query]
}

resource "aws_apigatewayv2_api" "http" {
  name          = "${var.project}-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = var.cors_origins
    allow_methods = ["POST", "OPTIONS"]
    allow_headers = ["content-type"]
    max_age       = 600
  }
}

resource "aws_apigatewayv2_integration" "query" {
  api_id                 = aws_apigatewayv2_api.http.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.query.invoke_arn
  payload_format_version = "2.0"
  timeout_milliseconds   = 30000
}

resource "aws_apigatewayv2_route" "ask" {
  api_id    = aws_apigatewayv2_api.http.id
  route_key = "POST /ask"
  target    = "integrations/${aws_apigatewayv2_integration.query.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.http.id
  name        = "$default"
  auto_deploy = true

  default_route_settings {
    throttling_rate_limit  = var.throttle_rate
    throttling_burst_limit = var.throttle_burst
  }
}

resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.query.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http.execution_arn}/*/*"
}
