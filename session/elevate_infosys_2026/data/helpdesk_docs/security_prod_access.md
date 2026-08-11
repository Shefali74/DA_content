# Production Environment Access Policy

## Overview
Access to the production environment is strictly controlled and requires multiple approvals. This policy ensures compliance with SOC 2 Type II and ISO 27001 requirements.

## Prerequisites for Production Access
Before requesting production access, you must:
1. Complete the mandatory Security Awareness Training (annual renewal required)
2. Pass the Production Environment Safety Assessment (score > 80%)
3. Have at least 30 days tenure in your current role
4. Acknowledge the Production Access Agreement

## Access Request Process

### Step 1: Training Verification
- Complete training at https://learning.internal/security-awareness
- Certificate is automatically recorded in your profile
- Training must be current (within last 12 months)

### Step 2: Manager Approval
- Submit access request via IT Portal > Security > Production Access
- Your direct manager reviews and approves the business justification
- Manager must be L6 or above

### Step 3: Security Review
- Security team reviews the request within 2 business days
- May request additional justification for sensitive systems
- Principle of least privilege applied: you get only what you need

### Step 4: Access Provisioning
- After all approvals: access provisioned within 1 business day
- You receive confirmation email with access details
- First login requires MFA setup specific to production

### Typical Turnaround: 3-5 business days

## Access Levels
| Level | Description | Approver |
|-------|-------------|----------|
| Read-Only | View logs, metrics, dashboards | Manager |
| Deploy | Push code through CI/CD pipeline | Manager + Tech Lead |
| Admin | Full system access, database queries | Manager + Security + VP |

## Emergency Access
- For production incidents (P1/P2): Break-glass procedure available
- Contact on-call SRE team via PagerDuty
- Emergency access logged and audited within 24 hours
- Requires post-incident justification

## Access Review
- Quarterly access review conducted by Security team
- Unused access (no login in 60 days) is automatically revoked
- Role changes trigger immediate access re-evaluation

## Violations
- Unauthorized access attempts are logged and reported
- Policy violations may result in disciplinary action
- All production actions are logged for audit trail

## Contact
Security Team: security@company.internal | Slack: #security-helpdesk
