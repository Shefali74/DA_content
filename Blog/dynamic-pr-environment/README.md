# Dynamic PR Environments with Lambda MicroVMs

Each PR gets its own isolated preview environment. Reviewers click a link in the PR comment. PR closes, everything is destroyed. Costs $0 when idle.

**Full walkthrough:** [I Built PR Preview Environments with AWS Lambda MicroVMs and Cut Staging Costs by 78%](https://dev.to/aws/i-built-pr-preview-environments-with-aws-lambda-microvms-and-cut-staging-costs-by-78-2d3i)

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        PR Opened / Push                              │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  GitHub Actions (OIDC → AWS)                                        │
│                                                                     │
│  1. zip code → S3                                                   │
│  2. update-microvm-image (builds new snapshot)                      │
│  3. terminate old MicroVM                                           │
│  4. run-microvm (starts from snapshot, <2s)                         │
│  5. generate access token → DynamoDB                                │
│  6. post preview URL to PR comment                                  │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Reviewer clicks PR link                                            │
│                                                                     │
│  Browser → Lambda Function URL (auth proxy)                         │
│         → validates token from DynamoDB                             │
│         → generates JWE auth token                                  │
│         → forwards request to MicroVM                               │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Lambda MicroVM (Flask app on port 8080)                            │
│                                                                     │
│  - Lifecycle hooks on port 9000 (/run, /suspend, /resume, /terminate)│
│  - App serves user traffic on port 8080                             │
│  - DynamoDB for PR-specific data (partitioned by PR#)               │
│  - Auto-suspends after 5 min idle                                   │
│  - Auto-resumes on next request (<2s)                               │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PR Closed                                                          │
│                                                                     │
│  GitHub Actions → terminate-microvm                                 │
│                → delete DynamoDB partition (PR#N)                    │
│                → delete S3 artifacts                                 │
└─────────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
dynamic-pr-environment/
├── microvm-image/
│   ├── app.py              # Flask app (port 8080) + lifecycle hooks (port 9000)
│   ├── Dockerfile          # Based on public.ecr.aws/lambda/microvms:al2023-minimal
│   └── requirements.txt
├── proxy/
│   └── handler.py          # Auth proxy Lambda (token validation + request forwarding)
├── infra/
│   ├── main.tf             # S3, DynamoDB, OIDC, IAM roles
│   ├── proxy.tf            # Proxy Lambda + Function URL
│   ├── variables.tf
│   └── outputs.tf
└── .github/workflows/
    ├── pr-deploy.yml        # Deploy on PR open/push
    └── pr-cleanup.yml       # Cleanup on PR close
```

## Prerequisites

- AWS account with Lambda MicroVMs access (us-east-1)
- Terraform >= 1.9
- Python 3.10+
- GitHub repo with Actions enabled

## Setup

### 1. Deploy Infrastructure

```bash
cd infra
cat <<EOF > terraform.tfvars
github_org  = "your-github-username"
github_repo = "your-repo-name"
EOF

terraform init
terraform apply
```

### 2. Configure GitHub Secrets

From `terraform output`, set these in repo Settings > Secrets:

| Secret | Value |
|--------|-------|
| `AWS_ROLE_ARN` | `github_actions_role_arn` output |
| `S3_BUCKET` | `s3_bucket_name` output |
| `MICROVM_BUILD_ROLE_ARN` | `microvm_build_role_arn` output |
| `MICROVM_EXECUTION_ROLE_ARN` | `microvm_execution_role_arn` output |
| `PROXY_URL` | `proxy_url` output |

### 3. Test

1. Create a branch, change any file under `Blog/dynamic-pr-environment/`
2. Open a PR to `master`
3. Wait for deploy workflow (~3 min first time)
4. Click the preview URL in the PR comment
5. Add/delete tasks to verify persistence
6. Close the PR to trigger cleanup

## Cost (5 devs, 40 PRs/month, 50 min active per PR)

| | Lambda MicroVMs | Shared Staging | EKS |
|---|---|---|---|
| **Total** | **$6.90/mo** | $31.65/mo | $104.65/mo |
| **Savings** | - | 78% | 93% |

Breakeven: ~5 hrs active per PR vs staging, ~16 hrs vs EKS.

## Tear Down

```bash
cd infra
terraform destroy
```
