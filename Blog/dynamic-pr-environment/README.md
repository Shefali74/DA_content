# Dynamic PR Environments with Lambda MicroVMs

Each PR gets its own isolated preview environment powered by AWS Lambda MicroVMs. Reviewers click a link in the PR comment and see the app running with that PR's code. PR closes, environment dies. Costs $0 when idle.

## What It Does

- PR opened/pushed: GitHub Actions builds a MicroVM image, runs it, posts a preview URL to the PR comment
- Reviewer clicks link: Auth proxy validates token, forwards to MicroVM
- 5 min idle: MicroVM auto-suspends ($0 compute). Reviewer comes back, resumes in <2s
- PR closed: MicroVM terminated, DynamoDB data deleted, S3 artifacts removed

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

From `terraform output`, set these in your repo Settings > Secrets and variables > Actions:

| Secret | Value |
|--------|-------|
| `AWS_ROLE_ARN` | `github_actions_role_arn` output |
| `S3_BUCKET` | `s3_bucket_name` output |
| `MICROVM_BUILD_ROLE_ARN` | `microvm_build_role_arn` output |
| `MICROVM_EXECUTION_ROLE_ARN` | `microvm_execution_role_arn` output |
| `PROXY_URL` | `proxy_url` output |

### 3. Test

1. Create a branch, make any change under `Blog/dynamic-pr-environment/`
2. Open a PR to `master`
3. Wait for the deploy workflow (~3 min first time)
4. Click the preview URL in the PR comment
5. Add/delete tasks to verify DynamoDB persistence
6. Close the PR to trigger cleanup

## How It Works

1. **Deploy**: GitHub Actions zips code to S3, calls `update-microvm-image` (builds snapshot), then `run-microvm` (starts in <2s). Stores access token in DynamoDB, posts preview URL to PR.
2. **Access**: Reviewer hits Lambda Function URL. Proxy validates token from DynamoDB, generates JWE auth token, forwards to MicroVM endpoint.
3. **Runtime**: Flask app on port 8080 serves the task manager. Lifecycle hooks on port 9000 handle `/run` (config injection), `/suspend`, `/resume`, `/terminate` (data cleanup).
4. **Cleanup**: PR closed triggers cleanup workflow. Terminates MicroVM, waits for TERMINATED state, deletes per-PR image, removes DynamoDB partition and S3 artifacts.

## Key Details

- **Per-PR images**: Each PR builds its own image (`pr-env-app-pr<number>`) to support parallel builds
- **Immutable deploys**: New push = new image = terminate old + run new. No hot-reload.
- **Auth**: Random 32-char hex token per PR stored in DynamoDB. Only people who see the PR comment have it.
- **ARM only**: Lambda MicroVMs run on Graviton (arm64). Python/Node/Go apps work fine.
- **Hooks on port 9000, app on port 8080**: Lambda routes user traffic to 8080. Hooks must be separate.

## Cost

For a team of 5 devs with 40 PRs/month, 50 min active per PR:

| Solution | Monthly Cost |
|----------|-------------|
| Lambda MicroVMs | ~$12 |
| Shared Staging (EC2 + ALB) | ~$56 |
| EKS (namespace per PR) | ~$201 |

MicroVMs run only 6.8% of the month. Suspended = $0 compute.

## Tear Down

```bash
cd infra
terraform destroy
```

## Blog Post

Full walkthrough: [Kill Your Staging Environment: Dynamic PR Previews with Lambda MicroVMs](link-to-blog)
