# Developer Onboarding and Environment Setup

## Day 1 Checklist
- [ ] Collect laptop from IT desk (Floor 3, Room 312)
- [ ] Activate corporate email account
- [ ] Set up MFA (Microsoft Authenticator recommended)
- [ ] Join required Teams/Slack channels
- [ ] Complete Day 1 orientation module

## Development Environment Setup

### Required Tools
1. **IDE**: VS Code (standard) or IntelliJ IDEA (for Java teams)
   - Download from IT Software Catalog: https://itportal.internal/software
   - Extensions/plugins list provided by your tech lead

2. **Git and Source Control**
   - Repository access: Request via IT Portal > Dev Tools > Repository Access
   - GitHub Enterprise: https://github.company.internal
   - Standard branching model: GitFlow (main, develop, feature/*, release/*)

3. **Container Tools**
   - Docker Desktop: Licensed via corporate agreement
   - Download from Software Catalog (requires manager approval due to licensing)
   - Kubernetes access: Provided for dev/staging clusters only

4. **Cloud Access (AWS)**
   - AWS SSO access: Request via Cloud Team portal
   - Dev account access: auto-provisioned for engineering roles
   - Staging access: Requires team lead approval
   - Production access: See Production Access Policy (separate document)

### CI/CD Pipeline
- All teams use GitHub Actions for CI/CD
- Pipeline templates available at: github.company.internal/platform/ci-templates
- Standard stages: Build > Test > Security Scan > Deploy to Staging > Deploy to Prod
- Deployment to production requires: 2 code reviewer approvals + passing all checks

### Code Review Standards
- All changes require at least 2 approvals
- Security-sensitive code requires Security team review
- PR descriptions must include: What, Why, How, and Testing Done sections
- Maximum PR size: 400 lines (break larger changes into smaller PRs)

## Common Issues

### "Cannot clone repository - access denied"
1. Verify your GitHub Enterprise account is active
2. Check if SSH key is added: Settings > SSH and GPG keys
3. If using HTTPS, ensure credential helper is configured
4. Contact your tech lead to verify team membership

### "Docker Desktop not starting"
1. Ensure Hyper-V/WSL2 is enabled (Windows) or Rosetta is installed (Mac M-series)
2. Check IT Software Catalog for approved version
3. Restart after installation
4. If license issue: Contact IT (license pool managed centrally)

## Useful Links
- Internal Wiki: https://wiki.internal
- Engineering Handbook: https://handbook.internal/engineering
- Architecture Decision Records: https://github.company.internal/platform/adrs

## Contact
Developer Experience Team: devex@company.internal | Slack: #dev-onboarding
