# user_lifecycle_checklist.py
# v2 - Enterprise IAM Lifecycle & Governance Simulator
# Focus: Identity state, governance, risk awareness, auditability

import os
import json
import uuid
from datetime import datetime, timedelta


# 🔒 Roles requiring mandatory expiry
EXPIRY_REQUIRED_ROLES = [
    "intern",
    "contractor",
    "vendor",
    "partner",
    "temporary employee"
]

# 🔥 Privileged roles (risk indicator)
PRIVILEGED_ROLES = [
    "it admin",
    "lead engineer",
    "cloud admin"
]


# -------------------------
# USER INPUT
# -------------------------

def get_user_details():
    print("\nEnter user details:")
    name = input("Employee Name: ").strip()
    email = input("Email Address: ").strip()
    department = input("Department: ").strip()
    role = input("Role: ").strip().lower()
    manager = input("Manager Name: ").strip()
    date = input("Start Date / Last Working Day: ").strip()

    return {
        "name": name,
        "email": email,
        "department": department,
        "role": role,
        "manager": manager,
        "date": date
    }


# -------------------------
# ROLE TASK MAPPING (RBAC)
# -------------------------

def get_role_tasks(role):
    ROLE_TASKS = {
        "designer": [
            "Provision email and collaboration tools",
            "Assign company device",
            "Apply security baseline"
        ],
        "engineer": [
            "Create identity account",
            "Assign role-based access groups",
            "Enable MFA",
            "Provision email and collaboration tools",
            "Assign company device",
            "Apply security baseline"
        ],
        "hr": [
            "Create identity account",
            "Assign HR systems access",
            "Enable MFA",
            "Provision email and collaboration tools"
        ],
        "intern": [
            "Provision limited email access",
            "Assign temporary device",
            "Apply security baseline",
            "Set account expiration date"
        ],
        "contractor": [
            "Provision restricted email access",
            "Grant project-specific access only",
            "Enable MFA",
            "Set automatic account expiry"
        ]
    }

    return ROLE_TASKS.get(role.lower(), [])


# -------------------------
# GOVERNANCE SUMMARY BLOCK
# -------------------------

def governance_summary(user, expiry_date):
    access_type = "Temporary" if expiry_date else "Permanent"
    expiry_info = expiry_date if expiry_date else "Not Applicable"

    return f"""## 🛡️ Governance Summary
- Role: {user['role']}
- Access Type: {access_type}
- Access Expiry: {expiry_info}
- Privileged Role: {user['role'] in PRIVILEGED_ROLES}
- Policy Model: Least privilege with deny-by-default
"""


# -------------------------
# CHECKLIST GENERATORS
# -------------------------

def onboarding_checklist(user, timestamp, expiry_date):
    tasks = get_role_tasks(user["role"])

    task_section = "\n".join([f"- [ ] {task}" for task in tasks]) if tasks else (
        "- [ ] 🚫 No access provisioned by default\n"
        "- [ ] Manual role verification required\n"
        "- [ ] Manager + Security approval required\n"
        "- [ ] Access granted only after approval"
    )

    return f"""# User Onboarding Checklist

## User Information
- Name: {user['name']}
- Email: {user['email']}
- Department: {user['department']}
- Role: {user['role']}
- Manager: {user['manager']}
- Start Date: {user['date']}

## Execution Metadata
- Action Type: Onboarding
- Generated On: {timestamp}

{governance_summary(user, expiry_date)}

## IT & Security Tasks
{task_section}

Security Guardrail:
Access is provisioned strictly based on role definition.
"""


def offboarding_checklist(user, timestamp):
    return f"""# User Offboarding Checklist

## User Information
- Name: {user['name']}
- Email: {user['email']}
- Department: {user['department']}
- Role: {user['role']}
- Manager: {user['manager']}
- Last Working Day: {user['date']}

## Execution Metadata
- Action Type: Offboarding
- Generated On: {timestamp}

## IT & Security Tasks
- [ ] Disable identity account
- [ ] Remove from access groups
- [ ] Revoke active sessions
- [ ] Collect company devices
- [ ] Archive user data
- [ ] Rotate shared credentials
- [ ] Log offboarding completion

Security Guardrail:
All access must be revoked before end of last working day.
"""


# -------------------------
# AUDIT LOGGING
# -------------------------

def write_audit_log(entry):
    log_dir = "automation/logs"
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, "audit_log.json")

    logs = []
    if os.path.exists(log_file):
        with open(log_file, "r") as file:
            try:
                logs = json.load(file)
            except json.JSONDecodeError:
                logs = []

    logs.append(entry)

    with open(log_file, "w") as file:
        json.dump(logs, file, indent=4)


# -------------------------
# OVERDUE REVIEW DETECTION
# -------------------------

def check_overdue_reviews():
    log_file = "automation/logs/audit_log.json"
    if not os.path.exists(log_file):
        return

    with open(log_file, "r") as file:
        try:
            logs = json.load(file)
        except json.JSONDecodeError:
            return

    today = datetime.now().date()
    overdue = []

    for entry in logs:
        if (
            entry.get("access_review_required")
            and entry.get("review_status") == "pending"
            and entry.get("review_due_by")
        ):
            due_date = datetime.strptime(entry["review_due_by"], "%Y-%m-%d").date()
            if due_date < today:
                overdue.append(entry)

    if overdue:
        print("\n⚠️ Governance Alert: Overdue Access Reviews")
        for item in overdue:
            print(f"- {item['user_email']} | Review ID: {item['review_id']} | Due: {item['review_due_by']}")


# -------------------------
# MAIN EXECUTION
# -------------------------

def main():

    print("Enterprise IAM Lifecycle Simulator v2")
    check_overdue_reviews()

    print("\nSelect execution mode:")
    print("1. Execute")
    print("2. Dry-run")

    mode = input("Select mode (1 or 2): ").strip()
    if mode not in ["1", "2"]:
        print("Invalid mode.")
        return

    dry_run = (mode == "2")

    print("\n1. Onboarding")
    print("2. Offboarding")

    choice = input("Select an option (1 or 2): ").strip()
    if choice not in ["1", "2"]:
        print("Invalid selection.")
        return

    user = get_user_details()
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")

    expiry_date = input(
        "Access Expiry Date (YYYY-MM-DD) [optional, required for temporary roles]: "
    ).strip()
    expiry_date = expiry_date if expiry_date else None

    # -------------------------
    # POLICY CLASSIFICATION
    # -------------------------

    if choice == "1":

        if user["role"] in EXPIRY_REQUIRED_ROLES and not expiry_date:
            role_policy_applied = "temporary_role_missing_expiry"
        elif user["role"] in EXPIRY_REQUIRED_ROLES and expiry_date:
            role_policy_applied = "temporary_role_with_expiry"
        elif get_role_tasks(user["role"]):
            role_policy_applied = "standard_role_matched"
        else:
            role_policy_applied = "role_not_defined_manual_review"

        # Enforce expiry requirement
        if role_policy_applied == "temporary_role_missing_expiry":
            print("\n❌ Expiry required for temporary role.")
            audit_entry = {
                "timestamp": timestamp,
                "identity_state": "provision_blocked",
                "action": "onboarding",
                "user_email": user["email"],
                "department": user["department"],
                "role": user["role"],
                "role_policy_applied": role_policy_applied
            }

            if dry_run:
                print(json.dumps(audit_entry, indent=4))
            else:
                write_audit_log(audit_entry)

            return

        if role_policy_applied == "role_not_defined_manual_review":
            identity_state = "active_with_restrictions"
        else:
            identity_state = "active"


        access_review_required = True
        review_due_by = expiry_date if expiry_date else (
            datetime.now() + timedelta(days=180)
        ).strftime("%Y-%m-%d")

        review_id = f"AR-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        review_status = "pending"
        review_generated_at = timestamp

    else:
        role_policy_applied = "offboarding"
        identity_state = "revoked"
        access_review_required = False
        review_due_by = None
        review_id = None
        review_status = None
        review_generated_at = None

    # -------------------------
    # FILE GENERATION
    # -------------------------

    output_dir = "automation/output"
    os.makedirs(output_dir, exist_ok=True)

    safe_name = user["name"].replace(" ", "_").lower()

    if choice == "1":
        content = onboarding_checklist(user, timestamp, expiry_date)
        filename = f"onboarding_{safe_name}_{timestamp}.md"
    else:
        content = offboarding_checklist(user, timestamp)
        filename = f"offboarding_{safe_name}_{timestamp}.md"

    file_path = os.path.join(output_dir, filename)

    if not dry_run:
        with open(file_path, "w") as file:
            file.write(content)

    # -------------------------
    # FINAL AUDIT ENTRY
    # -------------------------

    audit_entry = {
        "timestamp": timestamp,
        "identity_state": identity_state,
        "action": "onboarding" if choice == "1" else "offboarding",
        "user_email": user["email"],
        "department": user["department"],
        "role": user["role"],
        "privileged_access": user["role"] in PRIVILEGED_ROLES,
        "role_policy_applied": role_policy_applied,
        "generated_file": file_path if not dry_run else None,
        "access_expiry": expiry_date if expiry_date else "none",
        "access_review_required": access_review_required,
        "review_due_by": review_due_by,
        "review_id": review_id,
        "review_status": review_status,
        "review_generated_at": review_generated_at
    }

    if dry_run:
        print(json.dumps(audit_entry, indent=4))
    else:
        write_audit_log(audit_entry)
        print("\nOperation completed successfully.")
        print(file_path)


if __name__ == "__main__":
    main()
