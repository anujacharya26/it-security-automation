# IT & Security Automation

This repository contains practical automation projects focused on
real-world IT and security operations.

## 🎯 Goals
- Reduce manual effort in IT operations
- Standardize onboarding and offboarding
- Improve security posture through automation
- Minimize human error and blast radius

## 📂 Current Projects

### 1. User Lifecycle Automation
Automates onboarding and offboarding checklists for IT & security teams.

**Key concepts:**
- Least privilege
- RBAC
- Audit readiness
- Human-error reduction

## 🧾 Audit Logging & Traceability

Automation without traceability creates risk.

In real-world IT & security operations, every onboarding and offboarding action must be auditable.  
This project prioritizes **audit readiness** alongside automation.

### What is logged
Each execution of the script generates an audit entry containing:

- Timestamp of execution
- Action type (onboarding or offboarding)
- User email
- Department and role
- Generated checklist file reference

### Why audit logging matters
Audit logs enable teams to:

- Investigate incidents and access issues
- Prove compliance during audits
- Identify who performed which action and when
- Reduce blame-based investigations by providing facts

Without audit logs, automation becomes a black box.

### How it works
Audit data is written to a structured JSON file:

### Dry-Run Mode

The tool supports a dry-run mode to safely preview actions before execution.

In dry-run mode:
- No checklist files are created
- No audit logs are written
- The script prints a preview of what would happen

This is useful for:
- Validating changes
- Reducing blast radius
- Supporting change management approvals

## 🛠️ Tech Stack
- Python
- Markdown
- GitHub
- Future: APIs, IAM, Cloud, AI Ops

## 📌 Audience
- IT Engineers
- Security Analysts
- Cloud & IAM Practitioners
- Anyone learning real-world automation

> This repo is built as a learning-by-doing project and will evolve over time.
