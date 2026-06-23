# IT & Security Automation

This repository contains practical automation projects focused on real-world IT and security operations — built to reduce manual effort, enforce governance policies, and produce tamper-evident audit trails.

---

## 🎯 Goals

- Reduce manual effort in IT operations
- Standardize onboarding and offboarding
- Improve security posture through automation
- Minimize human error and blast radius
- Enforce governance controls with audit-grade logging

---

## 📂 Current Projects

### 1. User Lifecycle Automation — `user_lifecycle_checklist_v4.py`

Automates onboarding and offboarding checklists for IT and security teams. Built around a **deny-by-default, least-privilege** model with governance controls enforced at every step.

**Key concepts:**
- Least privilege
- RBAC
- Audit readiness
- Human-error reduction
- Risk-based governance

---

## 🔐 Security Principles Applied

This project is designed using real-world security principles, including:

- **Least Privilege** — Users receive only role-appropriate access
- **Default Deny** — Unknown roles fail safely and require manual review
- **Guardrails over Guessing** — Automation never assumes access
- **Audit-First Design** — Every action is traceable
- **Blast Radius Reduction** — Dry-run mode and RBAC limit the impact of mistakes
- **Dual Approval** — Privileged and contractor roles require manager + security sign-off before activation
- **Mandatory Expiry** — Temporary roles are blocked from provisioning without an expiry date

---

## 🚀 Features (v4.1)

| Feature | Description |
|---|---|
| Role-based provisioning | Automatically maps roles to provisioning task checklists |
| Privileged access detection | Flags elevated roles (`it admin`, `lead engineer`, `cloud admin`) |
| Dual-approval workflow | Suspends accounts pending manager + security sign-off for sensitive roles |
| Temporary role enforcement | Blocks provisioning if expiry date is missing for contractors, interns, vendors |
| Risk scoring engine | Computes a numeric governance risk score per identity |
| Risk classification | Classifies identities as `LOW`, `MEDIUM`, `HIGH`, or `CRITICAL` |
| Access review scheduling | Auto-schedules periodic reviews with unique tracking IDs |
| Overdue review alerts | Surfaces overdue access reviews at startup |
| Dry-run mode | Previews audit entry without writing files or logs |
| Append-only audit log | Every lifecycle event written to `automation/logs/audit_log.json` |
| Markdown checklist output | Generates per-user `.md` checklists saved to `automation/output/` |

---

## ⚖️ Risk Scoring Model

Risk scores are calculated per identity at provisioning time based on weighted governance factors:

| Factor | Weight | Rationale |
|---|---|---|
| Base (known role) | +20 | Minimum overhead for any catalogued identity |
| Privileged access | +50 | Largest blast radius if compromised |
| Temporary / expiry-bound | +15 | Requires active monitoring to ensure timely closure |
| Unknown role | +30 | Cannot be auto-scoped — forces manual review |
| Dual-approval required | +0 | Already captured by privileged/expiry flags |

### Risk Tiers

| Score Range | Level | Governance Response |
|---|---|---|
| 0 – 29 | `LOW` | Standard provisioning, no review required |
| 30 – 59 | `MEDIUM` | Access review scheduled at 180 days |
| 60 – 79 | `HIGH` | Dual-approval required, review at expiry or 180 days |
| 80+ | `CRITICAL` | Dual-approval required, immediate review scheduling |

### Validated Test Cases

| Role Input | Expiry | Score | Level |
|---|---|---|---|
| `engineer` | None | 20 | `LOW` |
| `contractor` | 2026-12-01 | 35 | `MEDIUM` |
| `lead engineer` | None | 70 | `HIGH` |
| `cloud admin, contractor` | 2026-12-01 | 85 | `CRITICAL` |

---

## 🗂️ Provisioning Catalogue

Roles with defined provisioning task lists (as of v4.1):

`designer` · `engineer` · `lead engineer` · `hr` · `intern` · `contractor` · `it admin` · `cloud admin`

Roles not in the catalogue trigger the **manual review workflow** — no access is granted automatically.

---

## 🚦 How to Run

```bash
cd automation
python3 user_lifecycle_checklist_v4.py
```

**Execution modes:**
- `1. Execute` — runs the workflow, writes checklist file and audit log
- `2. Dry-run` — previews the audit entry only, no files written

**Lifecycle actions:**
- `1. Onboarding` — provisions identity, applies governance controls
- `2. Offboarding` — generates revocation checklist, logs event

---

## 🧾 Audit Logging & Traceability

Automation without traceability creates risk.

In real-world IT and security operations, every onboarding and offboarding action must be auditable. This project prioritizes **audit readiness** alongside automation.

### What is logged

Each execution generates a structured audit entry containing:

- Timestamp of execution
- Action type (onboarding or offboarding)
- Identity state (`active`, `pending_approval`, `revoked`, `provision_blocked`)
- User email, department, and roles
- Privileged access flag
- Risk score and risk level
- Role policy applied
- Approval status (manager + security)
- Access expiry date
- Access review details (ID, due date, status)
- Generated checklist file reference

### Sample audit entry

```json
{
  "timestamp": "2026-06-23_11-40",
  "identity_state": "pending_approval",
  "action": "onboarding",
  "user_email": "john@example.com",
  "department": "Engineering",
  "roles": ["lead engineer"],
  "privileged_access": true,
  "risk_score": 70,
  "risk_level": "HIGH",
  "role_policy_applied": "standard_role_matched",
  "approval_required": true,
  "manager_approval_status": "pending",
  "security_approval_status": "pending",
  "access_expiry": "none",
  "access_review_required": true,
  "review_due_by": "2026-12-20",
  "review_id": "AR-20260623-97BC43",
  "review_status": "pending",
  "review_generated_at": "2026-06-23_11-40"
}
```

### Why audit logging matters

Audit logs enable teams to:

- Investigate incidents and access issues
- Prove compliance during audits (SOC 2, ISO 27001)
- Identify who performed which action and when
- Reduce blame-based investigations by providing facts

Without audit logs, automation becomes a black box.

---

## 🔄 Dry-Run Mode

The tool supports a dry-run mode to safely preview actions before execution.

In dry-run mode:
- No checklist files are created
- No audit logs are written
- The script prints a preview of what would happen

This is useful for:
- Validating changes before go-live
- Reducing blast radius
- Supporting change management approvals

---

## 📁 Repository Structure

```
it-security-automation/
├── automation/
│   ├── user_lifecycle_checklist_v4.py   # Main simulator (current version)
│   ├── onboarding_template.md           # Checklist template reference
│   ├── logs/
│   │   └── audit_log.json               # Append-only governance audit log
│   └── output/                          # Generated onboarding/offboarding checklists
├── docs/                                # Documentation
├── examples/                            # Example audit log outputs
└── README.md
```

---

## 🏢 Real-World Usage Context

In real organisations, similar automation is used to:

- Support IT service desks and security teams
- Enforce role-based access during onboarding
- Reduce incidents caused by over-permissioned users
- Improve audit and compliance readiness (SOC 2, ISO 27001)
- Standardize processes across distributed teams

This project intentionally mirrors enterprise patterns rather than shortcuts.

---

## 🛠️ Tech Stack

- Python 3
- Markdown
- GitHub
- Future: APIs, IAM integrations, Cloud, AI Ops

---

## 📌 Audience

- IT Engineers
- Security Analysts
- Cloud & IAM Practitioners
- Anyone learning real-world automation

---

## 🗺️ Roadmap (High-Level)

Planned enhancements include:

- Role-based offboarding logic
- Integration with identity providers (Okta, Azure AD)
- API-based automation
- Expanded audit metadata
- Cloud IAM alignment (AWS, Azure)
- Approval workflow notifications (email / Slack)
- Dashboard for overdue access reviews

The roadmap will evolve based on learning and real-world patterns.

---

## 🔖 Version History

| Version | Tag | Summary |
|---|---|---|
| v1 | — | Basic onboarding/offboarding checklist generator |
| v2 | — | Role-based task mapping, audit log introduced |
| v3 | — | Temporary role expiry enforcement, approval workflow |
| v4.0 | `v4.0` | Risk scoring engine, privileged access detection, dual-approval workflow |
| v4.1 | `v4.1` | Provisioning catalogue expanded (`lead engineer`, `it admin`, `cloud admin`); risk scoring calibrated to validated test cases; descriptive naming and intent comments added throughout |
