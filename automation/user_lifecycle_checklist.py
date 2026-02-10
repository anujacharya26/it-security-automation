# user_lifecycle_checklist.py
# v1 - Automation-assisted user onboarding and offboarding
# Focus: Standardization, auditability, and reduced human error

import os
import json
from datetime import datetime
# 🔒 Roles that require mandatory access expiry
EXPIRY_REQUIRED_ROLES = [
    "intern",
    "contractor",
    "vendor",
    "partner",
    "temporary employee"
]


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

def get_role_tasks(role):
    role = role.lower()

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
            "Provision email with limited access",
            "Assign temporary company device",
            "Apply security baseline",
            "Set account expiration date"
        ],
        "contractor": [
            "Provision email with restricted access",
            "Grant project-specific access only",
            "Enable MFA",
            "Set automatic account expiry"
        ]

    }

    return ROLE_TASKS.get(role, [])
def governance_summary(user, expiry_date):
    access_type = "Temporary" if expiry_date else "Permanent"
    expiry_info = expiry_date if expiry_date else "Not Applicable"

    return f"""## 🛡️ Governance Summary
- **Role:** {user['role']}
- **Access Type:** {access_type}
- **Access Expiry:** {expiry_info}
- **Policy Applied:** Least privilege with deny-by-default
"""

def onboarding_checklist(user, timestamp, expiry_date):
    tasks = get_role_tasks(user["role"])

    task_section = "\n".join([f"- [ ] {task}" for task in tasks]) if tasks else (
    "- [ ] 🚫 No access provisioned by default\n"
    "- [ ] Manual role verification required\n"
    "- [ ] Manager + Security approval required\n"
    "- [ ] Access granted only after approval"
    )

    return f"""# 🧑‍💼 User Onboarding Checklist

## User Information
- **Name:** {user['name']}
- **Email:** {user['email']}
- **Department:** {user['department']}
- **Role:** {user['role']}
- **Manager:** {user['manager']}
- **Start Date:** {user['date']}

## Execution Metadata
- **Action Type:** Onboarding
- **Generated On:** {timestamp}

{governance_summary(user, expiry_date)}

## ✅ IT & Security Tasks
{task_section}

⚠️ **Security Guardrail**
Access is provisioned strictly based on role.
Unrecognized roles require manual approval and audit logging.
"""

def offboarding_checklist(user, timestamp):
    return f"""# 🚫 User Offboarding Checklist

## User Information
- **Name:** {user['name']}
- **Email:** {user['email']}
- **Department:** {user['department']}
- **Role:** {user['role']}
- **Manager:** {user['manager']}
- **Last Working Day:** {user['date']}

## Execution Metadata
- **Action Type:** Offboarding
- **Generated On:** {timestamp}


## 🔐 IT & Security Tasks
- [ ] Disable identity account
- [ ] Remove from access groups
- [ ] Revoke active sessions
- [ ] Collect company devices
- [ ] Archive user data if required
- [ ] Rotate shared credentials (if applicable)
- [ ] Log offboarding completion

⚠️ **Security Guardrail**
Offboarding actions must be completed before end of last working day.
"""

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


def main():
    print("User Lifecycle Automation Tool (v1)")

    # 🔹 Dry-run selection (NEW, but does not change existing flow)
    print("\nSelect execution mode:")
    print("1. Execute (write files and audit logs)")
    print("2. Dry-run (preview only, no changes)")

    mode = input("Select mode (1 or 2): ").strip()

    if mode not in ["1", "2"]:
        print("Invalid mode. Exiting.")
        return

    dry_run = True if mode == "2" else False

    # 🔹 Existing onboarding/offboarding logic (UNCHANGED)
    print("\n1. Onboarding")
    print("2. Offboarding")

    choice = input("Select an option (1 or 2): ").strip()

    if choice not in ["1", "2"]:
        print("Invalid selection. Exiting.")
        return

    user = get_user_details()
    # ✅ Timestamp must come early
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    # 🔹 Optional access expiry (governance data collection)
    expiry_date = input(
        "Access Expiry Date (YYYY-MM-DD) [optional, required for temporary roles]: "
    ).strip()

    expiry_date = expiry_date if expiry_date else None
        # 🔒 Enforce expiry for temporary roles
    if choice == "1" and user["role"] in EXPIRY_REQUIRED_ROLES and not expiry_date:
        print("\n❌ Access expiry is required for this role.")
        print(f"Role '{user['role']}' requires a time-bound access expiry.")

        audit_entry = {
            "timestamp": timestamp,
            "action": "onboarding" if choice == "1" else "offboarding",
            "user_email": user["email"],
            "department": user["department"],
            "role": user["role"],
            "role_policy_applied": "expiry_required_missing",
            "generated_file": None
        }

        if dry_run:
            print("\n[DRY-RUN] Execution blocked due to missing expiry.")
            print(json.dumps(audit_entry, indent=4))
        else:
            write_audit_log(audit_entry)

        return

    output_dir = "automation/output"
    os.makedirs(output_dir, exist_ok=True)

    safe_name = user["name"].replace(" ", "_").lower()

    if choice == "1":
        content = onboarding_checklist(user, timestamp, expiry_date)
        filename = f"onboarding_{safe_name}_{timestamp}.md"
    else:
        content = offboarding_checklist(user, timestamp,)
        filename = f"offboarding_{safe_name}_{timestamp}.md"

    file_path = os.path.join(output_dir, filename)

    # 🔹 File write guarded by dry-run
    if dry_run:
        print("\n[DRY-RUN] Checklist would be generated at:")
        print(file_path)
    else:
        with open(file_path, "w") as file:
            file.write(content)

        print("\nChecklist generated successfully:")
        print(file_path)

    # 🔹 Audit log entry (UNCHANGED structure)
    audit_entry = {
        "timestamp": timestamp,
        "action": "onboarding" if choice == "1" else "offboarding",
        "user_email": user["email"],
        "department": user["department"],
        "role": user["role"],
        "role_policy_applied": "matched" if get_role_tasks(user["role"]) else "manual_review",
        "generated_file": file_path,
        "access_expiry": expiry_date if expiry_date else "none"

    }

    # 🔹 Audit log guarded by dry-run
    if dry_run:
        print("\n[DRY-RUN] Audit log entry preview:")
        print(json.dumps(audit_entry, indent=4))
    else:
        write_audit_log(audit_entry)


if __name__ == "__main__":
    main()
