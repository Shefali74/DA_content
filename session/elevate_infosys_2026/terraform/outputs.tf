output "knowledge_base_id" {
  description = "Bedrock Knowledge Base ID"
  value       = aws_bedrockagent_knowledge_base.helpdesk.id
}

output "guardrail_id" {
  description = "Bedrock Guardrail ID"
  value       = aws_bedrock_guardrail.helpdesk.guardrail_id
}

output "guardrail_version" {
  description = "Bedrock Guardrail Version"
  value       = aws_bedrock_guardrail_version.helpdesk_v1.version
}

output "s3_bucket_name" {
  description = "S3 bucket for KB documents"
  value       = aws_s3_bucket.kb_docs.id
}
