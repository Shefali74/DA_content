# Amazon Bedrock - Production Patterns Demo

> Building Generative AI Applications at Production Scale
> AWS Elevate Days 2026

## What This Is

A hands-on demo showing how to build a production-grade **IT Helpdesk Agent** using Amazon Bedrock. Each script demonstrates a specific production pattern with real cost implications.

## Features Demonstrated

| # | Feature | What It Shows | Production Lesson |
|---|---------|--------------|-------------------|
| 01 | Converse API + CRIS | Unified API, model switching, cross-region inference | Write code once, switch models for cost/speed |
| 02 | CountTokens (Tokenizer) | Pre-flight cost estimation, prompt optimization | max_tokens default = silent budget killer |
| 03 | Knowledge Base (RAG) | Grounded responses with citations | No RAG = model invents company policies |
| 04 | Guardrails | PII masking, denied topics, prompt attack blocking | Safety layer independent of model choice |
| 05 | Model Evaluation | LLM-as-a-Judge (Sonnet evaluates Haiku) | Never deploy prompt changes without evaluating |
| 06 | Intelligent Prompt Routing | Auto-route simple vs complex queries | 30% cost savings, zero code change |
| 07 | Cost Calculator | Full token economics at scale | 5 optimizations that save $1000s/month |
| 08 | Observability | Invocation logging, CloudWatch, alarms | Enable logging DAY ONE for cost attribution |

## Architecture

```
                         +-------------------+
                         |   Streamlit UI    |
                         |   (Demo Launcher) |
                         +--------+----------+
                                  |
                    +-------------+-------------+
                    |                           |
           +-------v-------+          +--------v--------+
           | Converse API  |          | CountTokens API |
           | (Unified)     |          | (Cost Estimate) |
           +-------+-------+          +-----------------+
                   |
        +----------+----------+
        |          |          |
   +----v---+ +---v----+ +---v--------+
   | Sonnet | | Haiku  | | Prompt     |
   |        | |        | | Router     |
   +----+---+ +---+----+ +---+--------+
        |         |           |
        +----+----+-----------+
             |
    +--------v--------+     +----------------+
    | Knowledge Base  |     | Guardrails     |
    | (RAG + S3 Docs) |     | (Safety Layer) |
    +-----------------+     +----------------+
```

## Quick Start

### Prerequisites

- AWS account with Bedrock access (Claude Sonnet + Haiku enabled)
- AWS CLI configured (`aws login`)
- Python 3.12 (macOS: `brew install python@3.12`)
- Terraform 1.5+

### 1. Deploy Everything (Single Command)

```bash
# Clone and setup
git clone https://github.com/jatinmehrotra/bedrock-production-patterns.git
cd bedrock-production-patterns

# Login to AWS
aws login

# Run full setup (Terraform + Data Source + Ingestion)
bash scripts/setup.sh
```

### OR Manual Step-by-Step:

```bash
# Step 1: Deploy infrastructure
cd terraform
terraform init
terraform apply -auto-approve
terraform output -json > outputs.json

# Step 2: Install Python dependencies (Python 3.12 required)
cd ..
/opt/homebrew/bin/python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install "botocore[crt]"
pip install -r requirements.txt
```

### 2. Run Individual Demos (Terminal)

```bash
source .venv/bin/activate
cd demo

# Set environment (use values from terraform output)
export BEDROCK_KB_ID=<knowledge_base_id from output>
export BEDROCK_GUARDRAIL_ID=<guardrail_id from output>
export BEDROCK_GUARDRAIL_VERSION=<guardrail_version from output>
export AWS_REGION=us-east-1

# Run any script directly
python 01_converse_api.py
python 02_count_tokens.py
python 03_knowledge_base_rag.py
python 04_guardrails.py
python 05_model_evaluation.py
python 06_prompt_routing.py
python 07_cost_calculator.py
python 08_observability.py
```

### 3. Run Streamlit UI (Recommended for Presentation)

```bash
cd ..
streamlit run app.py
```

## Configuration

Set these environment variables (or let scripts read from Terraform outputs):

```bash
export AWS_REGION=us-east-1
export BEDROCK_KB_ID=<from terraform output>
export BEDROCK_GUARDRAIL_ID=<from terraform output>
export BEDROCK_GUARDRAIL_VERSION=<from terraform output>
```

## Tech Stack

- **IaC**: Terraform (S3, Guardrail, IAM, Knowledge Base)
- **KB Type**: Managed Knowledge Base (zero-config vector store)
- **Models**: Claude Sonnet 4 + Claude 3.5 Haiku
- **Demo UI**: Streamlit with real-time terminal output
- **Scripts**: Python 3.10+ with boto3 + rich

## Production Optimization Checklist

1. **Set max_tokens explicitly** - Default reserves model max (64K for Sonnet!)
2. **Use Intelligent Prompt Routing** - 30% savings, zero code changes
3. **Enable Cross-Region Inference** - Free availability boost
4. **Implement Guardrails** - Safety without model dependency
5. **Evaluate before deploying** - LLM-as-Judge catches regressions
6. **Monitor with CloudWatch** - Track InputTokenCount, OutputTokenCount, InvocationThrottles
7. **Use Prompt Caching** - 90% savings on repeated context

## Cost Estimate (1000 conversations/day)

| Strategy | Monthly Cost | Savings |
|----------|-------------|---------|
| All Sonnet (unoptimized) | ~$366 | baseline |
| Intelligent Routing (65% Haiku / 35% Sonnet) | ~$192 | 48% |
| Routing + Prompt Caching | ~$100 | 73% |

## What's Next (From Here)

- **Multimodal**: Use Nova Vision to understand screenshots/error images in support tickets
- **Fine-tuning/Distillation**: Distill Sonnet knowledge into Haiku for your domain
- **Data Automation**: Process invoices, receipts, documents at scale with BDA
- **DynamoDB Vector Search**: Unified operational + vector store (GA 2026)
- **AgentCore**: Managed hosting for production agents (MCP, A2A protocol support)

## Cleanup

```bash
cd terraform
terraform destroy -auto-approve
```

## Session Info

- **Event**: AWS Elevate Days 2026
- **Speaker**: Jatin Mehrotra (Developer Advocate, AWS)
- **Duration**: 1 hour (25 min theory + 30 min demo + 5 min wrap-up)
