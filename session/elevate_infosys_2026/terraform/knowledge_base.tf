# =============================================================================
# S3 Bucket for Knowledge Base Documents (Source Data)
# =============================================================================
resource "aws_s3_bucket" "kb_docs" {
  bucket        = "${var.project_name}-kb-docs-${data.aws_caller_identity.current.account_id}"
  force_destroy = true

  tags = {
    Project = var.project_name
  }
}

# Upload helpdesk documents
resource "aws_s3_object" "helpdesk_docs" {
  for_each = fileset("${path.module}/../data/helpdesk_docs", "*.md")

  bucket = aws_s3_bucket.kb_docs.id
  key    = "helpdesk_docs/${each.value}"
  source = "${path.module}/../data/helpdesk_docs/${each.value}"
  etag   = filemd5("${path.module}/../data/helpdesk_docs/${each.value}")

  content_type = "text/markdown"
}

# =============================================================================
# IAM Role for Knowledge Base
# =============================================================================
resource "aws_iam_role" "kb_role" {
  name = "${var.project_name}-kb-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "bedrock.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy" "kb_policy" {
  name = "${var.project_name}-kb-policy"
  role = aws_iam_role.kb_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "S3DataSourceAccess"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.kb_docs.arn,
          "${aws_s3_bucket.kb_docs.arn}/*"
        ]
      }
    ]
  })
}

# =============================================================================
# Bedrock Knowledge Base (MANAGED type - Bedrock handles everything)
# Imported from existing KB created via CLI
# =============================================================================
resource "aws_bedrockagent_knowledge_base" "helpdesk" {
  name     = "${var.project_name}-helpdesk-kb"
  role_arn = aws_iam_role.kb_role.arn

  knowledge_base_configuration {
    type = "MANAGED"
    managed_knowledge_base_configuration {
      embedding_model_type = "MANAGED"
    }
  }

  tags = {
    Project = var.project_name
  }
}

# =============================================================================
# Data Source + Ingestion via local-exec (not yet in Terraform provider)
# =============================================================================
resource "null_resource" "kb_data_source" {
  depends_on = [
    aws_bedrockagent_knowledge_base.helpdesk,
    aws_s3_object.helpdesk_docs
  ]

  triggers = {
    kb_id       = aws_bedrockagent_knowledge_base.helpdesk.id
    bucket_name = aws_s3_bucket.kb_docs.id
    # Re-run if docs change
    docs_hash = md5(join(",", [for k, v in aws_s3_object.helpdesk_docs : v.etag]))
  }

  provisioner "local-exec" {
    interpreter = ["bash", "-c"]
    command = <<-EOT
      set -e
      KB_ID="${aws_bedrockagent_knowledge_base.helpdesk.id}"
      BUCKET="${aws_s3_bucket.kb_docs.id}"
      ACCOUNT_ID="${data.aws_caller_identity.current.account_id}"

      echo "Waiting for KB to be ACTIVE..."
      sleep 15

      # Check if data source already exists
      EXISTING_DS=$(aws bedrock-agent list-data-sources --knowledge-base-id "$KB_ID" --query 'dataSourceSummaries[0].dataSourceId' --output text 2>/dev/null || echo "None")

      if [ "$EXISTING_DS" = "None" ] || [ -z "$EXISTING_DS" ]; then
        echo "Creating data source..."
        DS_RESPONSE=$(aws bedrock-agent create-data-source \
          --knowledge-base-id "$KB_ID" \
          --name "helpdesk-docs" \
          --data-source-configuration "{\"type\":\"MANAGED_KNOWLEDGE_BASE_CONNECTOR\",\"managedKnowledgeBaseConnectorConfiguration\":{\"connectorParameters\":{\"type\":\"S3\",\"version\":\"1\",\"connectionConfiguration\":{\"bucketName\":\"$BUCKET\",\"bucketOwnerAccountId\":\"$ACCOUNT_ID\"},\"filterConfiguration\":{\"inclusionPrefixes\":[\"helpdesk_docs/\"]}}}}")
        EXISTING_DS=$(echo "$DS_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['dataSource']['dataSourceId'])")
        echo "Data source created: $EXISTING_DS"
        echo "Waiting for data source to be AVAILABLE..."
        sleep 30
      else
        echo "Data source already exists: $EXISTING_DS"
      fi

      echo "Starting ingestion..."
      aws bedrock-agent start-ingestion-job --knowledge-base-id "$KB_ID" --data-source-id "$EXISTING_DS"
      echo "Ingestion started. Documents will be indexed in ~60 seconds."
    EOT
  }
}
