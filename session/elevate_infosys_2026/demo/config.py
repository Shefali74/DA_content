"""
Shared configuration for all demo scripts.
Update these values after running `terraform apply`.
"""
import os
import json

# ============================================================
# AWS Configuration
# ============================================================
REGION = os.environ.get("AWS_REGION", "us-east-1")

# ============================================================
# Model IDs - Claude family
# ============================================================
MODEL_SONNET = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
MODEL_HAIKU = "us.anthropic.claude-haiku-4-5-20251001-v1:0"

# Cross-Region Inference Profile
MODEL_SONNET_CRIS = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"

# Intelligent Prompt Router (routes between Sonnet and Haiku)
MODEL_PROMPT_ROUTER = "anthropic.claude:0"  # Default Anthropic router

# ============================================================
# Resource IDs (populated from Terraform outputs)
# ============================================================
KNOWLEDGE_BASE_ID = os.environ.get("BEDROCK_KB_ID", "YOUR_KB_ID_HERE")
GUARDRAIL_ID = os.environ.get("BEDROCK_GUARDRAIL_ID", "YOUR_GUARDRAIL_ID_HERE")
GUARDRAIL_VERSION = os.environ.get("BEDROCK_GUARDRAIL_VERSION", "DRAFT")

# ============================================================
# Pricing (per 1000 tokens) - Claude models as of 2026
# ============================================================
PRICING = {
    "claude-sonnet": {"input": 0.003, "output": 0.015},
    "claude-haiku": {"input": 0.0008, "output": 0.004},
}

# ============================================================
# Helper: Load Terraform outputs if available
# ============================================================
TF_OUTPUTS_FILE = os.path.join(os.path.dirname(__file__), "..", "terraform", "outputs.json")

def load_terraform_outputs():
    """Load resource IDs from terraform output -json file."""
    global KNOWLEDGE_BASE_ID, GUARDRAIL_ID, GUARDRAIL_VERSION
    if os.path.exists(TF_OUTPUTS_FILE):
        with open(TF_OUTPUTS_FILE) as f:
            outputs = json.load(f)
        KNOWLEDGE_BASE_ID = outputs.get("knowledge_base_id", {}).get("value", KNOWLEDGE_BASE_ID)
        GUARDRAIL_ID = outputs.get("guardrail_id", {}).get("value", GUARDRAIL_ID)
        GUARDRAIL_VERSION = outputs.get("guardrail_version", {}).get("value", GUARDRAIL_VERSION)

load_terraform_outputs()
