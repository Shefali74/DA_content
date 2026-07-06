# =============================================================================
# AUTH PROXY LAMBDA + FUNCTION URL — Browser-accessible proxy for MicroVM endpoints
# =============================================================================

# Build the proxy zip automatically when handler.py changes
resource "null_resource" "build_proxy_zip" {
  triggers = {
    handler_hash = filemd5("${path.module}/../proxy/handler.py")
  }

  provisioner "local-exec" {
    command = <<-EOT
      cd ${path.module}/../proxy
      rm -rf package handler.zip .build-venv
      # Use Python 3.10+ (required for boto3 with lambda-microvms service)
      # Try python3.12, python3.11, python3.10, then fall back to python3
      PYTHON=$(command -v python3.12 || command -v python3.11 || command -v python3.10 || command -v python3)
      echo "Using Python: $PYTHON ($($PYTHON --version))"
      $PYTHON -m venv .build-venv
      source .build-venv/bin/activate
      pip install --upgrade pip --quiet
      pip install "boto3>=1.35.0" --no-cache-dir --quiet --upgrade
      mkdir -p package
      pip install "boto3>=1.35.0" -t package/ --no-cache-dir --quiet --upgrade
      echo "Bundled boto3 version: $(python3 -c 'import importlib.metadata; print(importlib.metadata.version("boto3"))' 2>/dev/null || pip show boto3 | grep Version)"
      deactivate
      rm -rf .build-venv
      cp handler.py package/
      cd package && zip -r9 ../handler.zip * && cd ..
      rm -rf package
    EOT
  }
}

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
        Sid    = "DynamoDBTokenLookup"
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem"
        ]
        Resource = "arn:aws:dynamodb:us-east-1:*:table/pr-environments"
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
  source_code_hash = filebase64sha256("${path.module}/../proxy/handler.py")

  depends_on = [null_resource.build_proxy_zip]

  tags = {
    Project = var.project_name
  }
}

# Function URL (public, no auth)
resource "aws_lambda_function_url" "proxy" {
  function_name      = aws_lambda_function.proxy.function_name
  authorization_type = "NONE"
}

# Permission: allow public InvokeFunctionUrl
resource "aws_lambda_permission" "public_function_url" {
  statement_id           = "AllowPublicFunctionUrl"
  action                 = "lambda:InvokeFunctionUrl"
  function_name          = aws_lambda_function.proxy.function_name
  principal              = "*"
  function_url_auth_type = "NONE"
}

# Permission: allow public InvokeFunction (required for Function URL to work)
resource "aws_lambda_permission" "public_invoke" {
  statement_id  = "AllowPublicInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.proxy.function_name
  principal     = "*"
}
