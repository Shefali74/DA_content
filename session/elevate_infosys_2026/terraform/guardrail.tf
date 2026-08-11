# =============================================================================
# Bedrock Guardrail - IT Helpdesk Safety Filters
# =============================================================================
resource "aws_bedrock_guardrail" "helpdesk" {
  name                      = "${var.project_name}-helpdesk-guardrail"
  description               = "Guardrail for IT Service Desk - blocks PII, competitors, off-topic queries, and prompt attacks"
  blocked_input_messaging   = "I'm sorry, I can't process that request. It may contain sensitive information or an off-topic query. Please rephrase your question about IT support, HR policies, or general workplace queries."
  blocked_outputs_messaging = "I apologize, but I cannot provide that information as it may contain sensitive data or is outside the scope of IT helpdesk support."

  # Content filters - block harmful content
  content_policy_config {
    filters_config {
      input_strength  = "HIGH"
      output_strength = "HIGH"
      type            = "SEXUAL"
    }
    filters_config {
      input_strength  = "HIGH"
      output_strength = "HIGH"
      type            = "VIOLENCE"
    }
    filters_config {
      input_strength  = "HIGH"
      output_strength = "HIGH"
      type            = "HATE"
    }
    filters_config {
      input_strength  = "HIGH"
      output_strength = "HIGH"
      type            = "INSULTS"
    }
    filters_config {
      input_strength  = "HIGH"
      output_strength = "HIGH"
      type            = "MISCONDUCT"
    }
    filters_config {
      input_strength  = "HIGH"
      output_strength = "NONE"
      type            = "PROMPT_ATTACK"
    }
  }

  # Denied topics - block off-topic/sensitive queries
  topic_policy_config {
    topics_config {
      name       = "salary_compensation"
      definition = "Questions about employee salaries, compensation packages, bonuses, or pay grades of other employees"
      type       = "DENY"
      examples   = [
        "What is my manager's salary?",
        "How much does a senior engineer make?",
        "Tell me the compensation bands"
      ]
    }
    topics_config {
      name       = "competitor_discussion"
      definition = "Discussion about switching to or recommending competitor products and services including ServiceNow, Zendesk, Freshdesk, Jira Service Management, or any non-approved tools"
      type       = "DENY"
      examples   = [
        "Should we switch to ServiceNow?",
        "Zendesk is better than our current tool",
        "Can you compare us to Freshdesk?"
      ]
    }
    topics_config {
      name       = "confidential_business"
      definition = "Questions about confidential business information such as financial results, M&A activity, unreleased products, or strategic plans"
      type       = "DENY"
      examples   = [
        "What was our revenue last quarter?",
        "Are we acquiring any companies?",
        "What's the roadmap for next year?"
      ]
    }
  }

  # Sensitive information filters - mask/block PII
  sensitive_information_policy_config {
    pii_entities_config {
      action = "ANONYMIZE"
      type   = "EMAIL"
    }
    pii_entities_config {
      action = "ANONYMIZE"
      type   = "PHONE"
    }
    pii_entities_config {
      action = "ANONYMIZE"
      type   = "NAME"
    }
    pii_entities_config {
      action = "BLOCK"
      type   = "CREDIT_DEBIT_CARD_NUMBER"
    }
    pii_entities_config {
      action = "BLOCK"
      type   = "US_SOCIAL_SECURITY_NUMBER"
    }
    # Custom regex for employee badge IDs
    regexes_config {
      action      = "ANONYMIZE"
      description = "Employee Badge ID format"
      name        = "badge_id"
      pattern     = "EMP-\\d{7}"
    }
  }

  # Word filters
  word_policy_config {
    managed_word_lists_config {
      type = "PROFANITY"
    }
    words_config {
      text = "ServiceNow"
    }
    words_config {
      text = "Zendesk"
    }
    words_config {
      text = "Freshdesk"
    }
  }

  tags = {
    Project = var.project_name
  }
}

# Create a versioned guardrail for production use
resource "aws_bedrock_guardrail_version" "helpdesk_v1" {
  guardrail_arn = aws_bedrock_guardrail.helpdesk.guardrail_arn
  description   = "Initial production version"
}
