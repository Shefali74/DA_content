# =============================================================================
# AUTH PROXY LAMBDA — Browser-accessible proxy for MicroVM endpoints
# =============================================================================

# IAM Role for the proxy Lambda
resource "aws_iam_role" "proxy_lambda" {
  name = "${var.project_name}-proxy-lambda"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })

  tags = {
    Project = var.project_name
  }
}

resource "aws_iam_role_policy" "proxy_lambda" {
  name = "${var.project_name}-proxy-lambda-policy"
  role = aws_iam_role.proxy_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "MicroVMAccess"
        Effect = "Allow"
        Action = [
          "lambda:GetMicrovm",
          "lambda:CreateMicrovmAuthToken"
        ]
        Resource = "*"
      },
      {
        Sid    = "Logs"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      }
    ]
  })
}

# Lambda Function
resource "aws_lambda_function" "proxy" {
  function_name = "${var.project_name}-auth-proxy"
  role          = aws_iam_role.proxy_lambda.arn
  handler       = "handler.handler"
  runtime       = "python3.12"
  timeout       = 30
  memory_size   = 256

  filename         = "${path.module}/../proxy/handler.zip"
  source_code_hash = filebase64sha256("${path.module}/../proxy/handler.zip")

  tags = {
    Project = var.project_name
  }
}

# Function URL (public — no IAM auth, the proxy handles MicroVM auth internally)
resource "aws_lambda_function_url" "proxy" {
  function_name      = aws_lambda_function.proxy.function_name
  authorization_type = "NONE"
}

# Permission for Function URL to invoke Lambda
resource "aws_lambda_permission" "proxy_url" {
  statement_id           = "AllowFunctionURLInvoke"
  action                 = "lambda:InvokeFunctionUrl"
  function_name          = aws_lambda_function.proxy.function_name
  principal              = "*"
  function_url_auth_type = "NONE"
}
