# Production Checklist - Amazon Bedrock

## Before Going to Production

Use this checklist before deploying your Bedrock-powered application to production.

---

## 1. Cost Control

- [ ] **Set `maxTokens` explicitly on EVERY request**
  - Claude Sonnet default: 64,000 tokens reserved per request
  - For helpdesk/chatbot: `maxTokens: 500` is sufficient
  - This prevents silent TPM quota exhaustion

- [ ] **Enable Intelligent Prompt Routing**
  - Route simple queries to Haiku (4x cheaper than Sonnet)
  - Zero code changes - just swap model ID to router profile
  - Saves ~30% on mixed workloads

- [ ] **Optimize system prompts**
  - Use `CountTokens` API to measure before/after
  - Shorter prompt = fewer tokens per call = lower cost at scale
  - 100-word prompt vs 500-word prompt = 80% input token savings

- [ ] **Enable Prompt Caching** (for repeated context)
  - 90% cost reduction on cached content
  - 85% latency reduction
  - Best for: system prompts, RAG context, few-shot examples
  - 5-minute TTL (resets on each hit)

- [ ] **Use Cross-Region Inference (CRIS)**
  - No extra cost (same token pricing)
  - Higher availability (routes to available region)
  - Global profiles: additional 10% savings

---

## 2. Safety and Compliance

- [ ] **Deploy Guardrails**
  - Content filters (Hate, Violence, Sexual, Misconduct, Prompt Attack)
  - Denied topics (specific to your business)
  - PII masking (email, phone, SSN, custom patterns)
  - Word filters (competitors, profanity)

- [ ] **Version your Guardrails**
  - Test in DRAFT, deploy specific numbered version
  - Never point production to DRAFT

- [ ] **Apply Guardrails to ALL models**
  - Guardrails are model-agnostic
  - Use `ApplyGuardrail` API for pre-screening without model call

---

## 3. Quality Assurance

- [ ] **Set up LLM-as-a-Judge evaluation pipeline**
  - Stronger model evaluates weaker model's outputs
  - Define scoring criteria specific to YOUR use case
  - Set quality thresholds (e.g., average > 3.5/5)

- [ ] **Evaluate before deploying prompt changes**
  - Run evaluation batch on test dataset
  - Compare scores: new prompt vs current prompt
  - Automate in CI/CD pipeline

- [ ] **Use Knowledge Base for grounded responses**
  - Eliminates hallucinations about company-specific info
  - Citations provide audit trail
  - Keep KB docs updated (stale docs = wrong answers)

---

## 4. Observability

- [ ] **Enable Invocation Logging**
  - Logs to CloudWatch Logs and/or S3
  - Captures: identity.arn, modelId, inputTokenCount, outputTokenCount
  - Essential for cost attribution and chargeback

- [ ] **Set up CloudWatch Alarms**
  - `InvocationThrottles > 0` (any throttle = investigate)
  - `InputTokenCount > daily_budget` (cost overrun)
  - `InvocationLatency P99 > 10s` (user experience)
  - `InvocationServerErrors > 0` (reliability)

- [ ] **Create CloudWatch Dashboard**
  - Invocations/min by model
  - Token usage (input + output) over time
  - Latency P50/P95/P99
  - Cost by application (from invocation logs)
  - Throttle count (should always be 0)

- [ ] **Token attribution per application**
  - Use CloudWatch Logs Insights queries
  - Group by `identity.arn` to see which app/user burns tokens
  - Essential for multi-tenant cost allocation

---

## 5. Resilience

- [ ] **Implement exponential backoff with jitter**
  - On 429 (ThrottlingException): backoff + wait for 60s quota refresh
  - On 503 (ServiceUnavailable): immediate retry with backoff
  - Use AWS SDK built-in retry configuration

- [ ] **Ramp up traffic gradually**
  - Start at target RPM, reduce by 50% on 503 errors
  - Hold steady state 15 min, then increase 50%
  - Repeat until target volume reached

- [ ] **Enable Cross-Region Inference**
  - Automatic failover across regions
  - No extra cost, same API
  - Geographic or Global profiles available

- [ ] **Set appropriate timeouts**
  - HTTP timeout > expected max response time
  - For streaming: shorter initial byte timeout, longer full response timeout

---

## 6. Prompt Management

- [ ] **Version all prompts**
  - Use Bedrock Prompt Management or version control
  - Never modify production prompts without versioning

- [ ] **Compare prompt variants before deploying**
  - Test multiple versions with same input
  - Use Prompt Management's built-in comparison feature

---

## Quick Reference: Cost Per 1000 Conversations

| Strategy | Monthly Cost (1K conv/day) | Notes |
|----------|---------------------------|-------|
| All Sonnet (unoptimized) | ~$1,200 | Default trap |
| Intelligent Routing | ~$600 | 50% savings |
| Routing + Prompt Caching | ~$450 | 62% savings |
| Routing + Caching + Optimized Prompts | ~$350 | 71% savings |
