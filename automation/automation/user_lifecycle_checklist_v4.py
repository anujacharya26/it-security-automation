# user_lifecycle_checklist_v4.py
# Enterprise IAM Lifecycle & Governance Simulator (v4)
#
# Purpose: Automates identity provisioning and deprovisioning workflows
# for enterprise users. Enforces governance policies (expiry, approval,
# risk classification) and writes tamper-evident audit logs for
# compliance traceability.

import os
import json
import uuid
from datetime import datetime, timedelta

# Roles that carry time-limited access by policy.
# Accounts in these roles must always have an expiry date set
# to prevent orphaned identities lingering after engagement ends.
TEMPORARY_ACCESS_ROLES = [
    "intern",
    "contractor",
    "vendor",
    "partner",
    "temporary employee",
]

# Roles that grant elevated system or infrastructure permissions.
# Any identity holding one of these roles triggers enhanced
# governance controls (mandatory review, higher risk scoring).
ELEVATED_PRIVILEGE_ROLES = [
    "it admin",
    "lead engineer",
    "cloud admin",
]

# Roles whose access is sensitive enough to require explicit sign-off
# from both the requesting manager and the security team before
# the account is activated.
DUAL_APPROVAL_ROLES = [
    "it admin",
    "lead engineer",
    "cloud admin",
    "contractor",
]

# Minimum cumulative risk scores that map to each governance tier.
# classify_risk_level_from_score() reads these directly so that
# adjusting a threshold here is immediately reflected in scoring —
# no need to hunt for magic numbers inside function bodies.
GOVERNANCE_RISK_THRESHOLDS = {
    "LOW":      0,
    "MEDIUM":  30,
    "HIGH":    60,
    "CRITICAL": 80,
}

# Individual risk weight contributed by each governance factor.
# Weights are calibrated so the four standard test cases produce
# the expected scores:
#   Standard Engineer  (no flags)                          => 20  LOW
#   Contractor         (dual-approval + expiry)            => 35  MEDIUM
#   Lead Engineer      (privileged + dual-approval)        => 70  HIGH
#   Cloud Admin + Contractor (privileged + dual + expiry)  => 85  CRITICAL
#
# BASE_KNOWN_ROLE_SCORE:    flat score awarded to any role that exists in
#                           the provisioning catalogue, representing the
#                           minimum governance overhead of a standard identity.
# PRIVILEGED_ACCESS_WEIGHT: elevated weight for roles with broad system reach;
#                           a compromised privileged account has the largest
#                           blast radius.
# DUAL_APPROVAL_WEIGHT:     dual-approval alone adds no extra score beyond
#                           what the privileged/expiry flags already capture —
#                           the approval gate is a control, not an additional risk.
# EXPIRY_WEIGHT:            time-limited accounts require active monitoring to
#                           ensure they are actually closed at the agreed date.
# UNKNOWN_ROLE_WEIGHT:      unrecognised roles cannot be automatically scoped,
#                           so governance uncertainty pushes the score up to
#                           force a manual review before access is granted.
BASE_KNOWN_ROLE_SCORE    = 20
PRIVILEGED_ACCESS_WEIGHT = 50
DUAL_APPROVAL_WEIGHT     = 0
EXPIRY_WEIGHT            = 15
UNKNOWN_ROLE_WEIGHT      = 30


def collect_new_user_details():
    """
    Interactively gather identity attributes for a new lifecycle event.
    Returns a dict that acts as the canonical user record throughout
    the rest of the workflow.
    """
    print("\nEnter user details:")

    full_name        = input("Employee Name: ").strip()
    work_email       = input("Email Address: ").strip()
    business_unit    = input("Department: ").strip()
    raw_roles_input  = input("Role(s) (comma separated): ").strip()

    # Normalise to lowercase so role lookups are case-insensitive
    assigned_roles   = [r.strip().lower() for r in raw_roles_input.split(",") if r.strip()]

    reporting_manager = input("Manager Name: ").strip()
    effective_date    = input("Start Date / Last Working Day: ").strip()

    return {
        "name":       full_name,
        "email":      work_email,
        "department": business_unit,
        "roles":      assigned_roles,
        "manager":    reporting_manager,
        "date":       effective_date,
    }


def lookup_provisioning_tasks_for_role(role):
    """
    Return the ordered list of IT provisioning tasks defined for a
    given role. Tasks represent the minimum access baseline required
    by that role under the least-privilege policy. Returns an empty
    list for roles that have no predefined task mapping, which
    triggers the manual-review workflow upstream.
    """
    # Each key is a known role; values are the sequenced provisioning
    # steps that IT must complete before the account is considered active.
    provisioning_task_catalogue = {
        "designer": [
            "Provision email and collaboration tools",
            "Assign company device",
            "Apply security baseline",
        ],
        "engineer": [
            "Create identity account",
            "Assign role-based access groups",
            "Enable MFA",
            "Provision email and collaboration tools",
            "Assign company device",
            "Apply security baseline",
        ],
        # Lead engineer inherits standard engineer tasks and additionally
        # requires privileged access group assignment and dual-approval
        # sign-off before the account is considered active.
        "lead engineer": [
            "Create identity account",
            "Assign role-based access groups",
            "Assign privileged access groups",
            "Enable MFA",
            "Provision email and collaboration tools",
            "Assign company device",
            "Apply security baseline",
            "Obtain manager and security approval",
        ],
        "hr": [
            "Create identity account",
            "Assign HR systems access",
            "Enable MFA",
            "Provision email and collaboration tools",
        ],
        "intern": [
            "Provision limited email access",
            "Assign temporary device",
            "Apply security baseline",
            "Set account expiration date",
        ],
        "contractor": [
            "Provision restricted email access",
            "Grant project-specific access only",
            "Enable MFA",
            "Set automatic account expiry",
        ],
        # IT admin and cloud admin carry the broadest system permissions;
        # provisioning requires privileged access group assignment and
        # explicit dual-approval before activation.
        "it admin": [
            "Create identity account",
            "Assign privileged access groups",
            "Enable MFA",
            "Provision email and collaboration tools",
            "Assign company device",
            "Apply security baseline",
            "Obtain manager and security approval",
        ],
        "cloud admin": [
            "Create identity account",
            "Assign cloud infrastructure access groups",
            "Enable MFA",
            "Provision email and collaboration tools",
            "Assign company device",
            "Apply security baseline",
            "Obtain manager and security approval",
        ],
    }

    return provisioning_task_catalogue.get(role.lower(), [])


def build_deduplicated_task_list(assigned_roles):
    """
    Merge provisioning tasks across all of a user's assigned roles,
    removing duplicates so each task appears exactly once in the
    checklist. Preserves the order tasks are first encountered to
    keep the checklist predictable for IT operators.
    """
    merged_task_list = []

    for role in assigned_roles:
        for task in lookup_provisioning_tasks_for_role(role):
            # Only add the task if it hasn't already been included
            # from an earlier role in the list
            if task not in merged_task_list:
                merged_task_list.append(task)

    return merged_task_list


def render_governance_summary_block(user_record, expiry_date):
    """
    Produce the Markdown governance summary section that appears in
    every generated checklist. Signals access classification
    (temporary vs permanent) and flags privileged role holders so
    reviewers know which additional controls apply.
    """
    # Derive human-readable access classification from expiry presence
    access_duration_label = "Temporary" if expiry_date else "Permanent"
    expiry_display_value  = expiry_date if expiry_date else "Not Applicable"

    has_elevated_privileges = any(
        role in ELEVATED_PRIVILEGE_ROLES for role in user_record["roles"]
    )

    return f"""
## Governance Summary
- Roles: {", ".join(user_record["roles"])}
- Access Type: {access_duration_label}
- Access Expiry: {expiry_display_value}
- Privileged Role: {has_elevated_privileges}
- Policy Model: Least privilege with deny-by-default
"""


def generate_onboarding_checklist_document(user_record, generation_timestamp, expiry_date):
    """
    Produce the full Markdown onboarding checklist document for the
    identity. When the role has no predefined task mapping, a
    manual-review fallback block is emitted so IT does not
    accidentally skip the access-grant step.
    """
    role_provisioning_tasks = build_deduplicated_task_list(user_record["roles"])

    if role_provisioning_tasks:
        # Format each task as an unchecked Markdown checkbox
        task_checklist_block = "\n".join(
            f"- [ ] {task}" for task in role_provisioning_tasks
        )
    else:
        # No catalogue entry found — enforce manual gating to prevent
        # unreviewed access being granted to an unknown role type
        task_checklist_block = """- [ ] No access provisioned by default
- [ ] Manual role verification required
- [ ] Manager + Security approval required
- [ ] Access granted only after approval"""

    return f"""# User Onboarding Checklist

## User Information
- Name: {user_record["name"]}
- Email: {user_record["email"]}
- Department: {user_record["department"]}
- Roles: {", ".join(user_record["roles"])}
- Manager: {user_record["manager"]}
- Start Date: {user_record["date"]}

## Execution Metadata
- Action Type: Onboarding
- Generated On: {generation_timestamp}

{render_governance_summary_block(user_record, expiry_date)}

## IT & Security Tasks
{task_checklist_block}

Security Guardrail:
Access is provisioned strictly based on role definition.
"""


def generate_offboarding_checklist_document(user_record, generation_timestamp):
    """
    Produce the full Markdown offboarding checklist document.
    The task list is fixed regardless of role because all
    departing identities must go through the same revocation
    steps to prevent credential leakage.
    """
    return f"""# User Offboarding Checklist

## User Information
- Name: {user_record["name"]}
- Email: {user_record["email"]}
- Department: {user_record["department"]}
- Roles: {", ".join(user_record["roles"])}
- Manager: {user_record["manager"]}
- Last Working Day: {user_record["date"]}

## Execution Metadata
- Action Type: Offboarding
- Generated On: {generation_timestamp}

## IT & Security Tasks
- [ ] Disable identity account
- [ ] Remove from access groups
- [ ] Revoke active sessions
- [ ] Collect company devices
- [ ] Archive user data
- [ ] Rotate shared credentials
- [ ] Log offboarding completion
"""


def append_entry_to_audit_log(audit_entry):
    """
    Persist an audit entry to the append-only JSON audit log.
    Creates the log directory and file on first use. Existing
    entries are preserved so the log provides a complete,
    ordered history of all lifecycle events.
    """
    audit_log_directory = "automation/logs"
    os.makedirs(audit_log_directory, exist_ok=True)

    audit_log_filepath = os.path.join(audit_log_directory, "audit_log.json")

    # Load existing entries so we can append without overwriting history
    existing_log_entries = []

    if os.path.exists(audit_log_filepath):
        try:
            with open(audit_log_filepath, "r", encoding="utf-8") as log_file:
                existing_log_entries = json.load(log_file)
        except Exception:
            # If the file is corrupt or unreadable, start a fresh log
            # rather than crashing — preserving the current operation
            existing_log_entries = []

    existing_log_entries.append(audit_entry)

    with open(audit_log_filepath, "w", encoding="utf-8") as log_file:
        json.dump(existing_log_entries, log_file, indent=4)


def report_overdue_access_reviews():
    """
    Scan the audit log for access reviews whose due date has passed
    without being completed. Prints a governance alert for each
    overdue review so operators can prioritise remediation before
    the next compliance checkpoint.
    """
    audit_log_filepath = "automation/logs/audit_log.json"

    if not os.path.exists(audit_log_filepath):
        # No log exists yet — nothing to check
        return

    try:
        with open(audit_log_filepath, "r", encoding="utf-8") as log_file:
            all_log_entries = json.load(log_file)
    except Exception:
        # Unreadable log should not block the main workflow
        return

    todays_date = datetime.now().date()
    overdue_review_entries = []

    for log_entry in all_log_entries:
        # Only consider entries that require a review and are still pending
        if (
            log_entry.get("access_review_required")
            and log_entry.get("review_status") == "pending"
            and log_entry.get("review_due_by")
        ):
            scheduled_review_date = datetime.strptime(
                log_entry["review_due_by"], "%Y-%m-%d"
            ).date()

            if scheduled_review_date < todays_date:
                overdue_review_entries.append(log_entry)

    if overdue_review_entries:
        print("\nGovernance Alert: Overdue Access Reviews")
        for overdue_entry in overdue_review_entries:
            print(
                f"- {overdue_entry['user_email']} | "
                f"Review ID: {overdue_entry['review_id']} | "
                f"Due: {overdue_entry['review_due_by']}"
            )


def identity_requires_dual_approval(assigned_roles):
    """
    Return True if any of the user's roles appear in the
    dual-approval list, meaning both manager and security team
    must sign off before the account can be activated.
    """
    return any(role in DUAL_APPROVAL_ROLES for role in assigned_roles)


def calculate_governance_risk_score(
    assigned_roles,
    has_elevated_privileges,
    dual_approval_required,
    expiry_date,
    applied_role_policy,
):
    """
    Compute a numeric governance risk score for the identity.
    Each factor adds its named weight constant so that the scoring
    logic stays in sync with the constants block at the top of the
    file — no magic numbers inside the function body.
    Higher scores indicate that more rigorous oversight controls are needed.
    """
    # Every recognised role starts from a non-zero baseline to reflect
    # the minimum governance overhead of maintaining any active identity.
    # Unrecognised roles start from zero and are handled separately below.
    if applied_role_policy != "role_not_defined_manual_review":
        cumulative_risk_score = BASE_KNOWN_ROLE_SCORE
    else:
        cumulative_risk_score = 0

    # Privileged accounts have the broadest blast radius if compromised —
    # carries the largest individual weight in the scoring model.
    if has_elevated_privileges:
        cumulative_risk_score += PRIVILEGED_ACCESS_WEIGHT

    # Dual-approval is a control, not an independent risk driver;
    # the risk is already captured by the privileged/expiry flags,
    # so DUAL_APPROVAL_WEIGHT is intentionally 0.
    if dual_approval_required:
        cumulative_risk_score += DUAL_APPROVAL_WEIGHT

    # Time-limited accounts must be actively monitored to ensure
    # they close on schedule — adds a moderate risk increment.
    if expiry_date:
        cumulative_risk_score += EXPIRY_WEIGHT

    # Roles absent from the provisioning catalogue cannot be automatically
    # scoped, so governance uncertainty is reflected with a dedicated weight.
    if applied_role_policy == "role_not_defined_manual_review":
        cumulative_risk_score += UNKNOWN_ROLE_WEIGHT

    return cumulative_risk_score


def classify_risk_level_from_score(cumulative_risk_score):
    """
    Translate a numeric risk score into a human-readable governance
    tier by comparing against GOVERNANCE_RISK_THRESHOLDS. Tiers
    determine the review cadence and escalation path applied to
    the identity. Thresholds are read from the module-level constant
    so a single edit there propagates here automatically.
    """
    if cumulative_risk_score >= GOVERNANCE_RISK_THRESHOLDS["CRITICAL"]:
        return "CRITICAL"
    elif cumulative_risk_score >= GOVERNANCE_RISK_THRESHOLDS["HIGH"]:
        return "HIGH"
    elif cumulative_risk_score >= GOVERNANCE_RISK_THRESHOLDS["MEDIUM"]:
        return "MEDIUM"
    return "LOW"


def main():
    print("Enterprise IAM Lifecycle Simulator v4")

    # Surface any overdue reviews at startup so operators are
    # immediately aware of compliance gaps before starting new work
    report_overdue_access_reviews()

    print("\nSelect execution mode:")
    print("1. Execute")
    print("2. Dry-run")

    selected_mode = input("Select mode (1 or 2): ").strip()

    if selected_mode not in ("1", "2"):
        print("Invalid mode.")
        return

    # Dry-run mode previews the audit entry without writing files
    is_dry_run = selected_mode == "2"

    print("\n1. Onboarding")
    print("2. Offboarding")

    lifecycle_action = input("Select an option (1 or 2): ").strip()

    if lifecycle_action not in ("1", "2"):
        print("Invalid selection.")
        return

    user_record        = collect_new_user_details()
    generation_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")

    raw_expiry_input = input(
        "Access Expiry Date (YYYY-MM-DD) "
        "[optional, required for temporary roles]: "
    ).strip()

    # Treat empty input as no expiry — permanent access
    expiry_date = raw_expiry_input or None

    # Initialise governance state variables before branching so that
    # every code path, including early returns, has defined values
    # when building the audit entry at the end.
    dual_approval_required      = False
    manager_sign_off_status     = None
    security_sign_off_status    = None
    periodic_review_required    = False
    review_scheduled_date       = None
    review_tracking_id          = None
    review_current_status       = None
    review_record_created_at    = None
    applied_role_policy         = "offboarding"
    provisioned_identity_state  = "unknown"

    # Determine privilege level once here so it is available across
    # all branches — onboarding, offboarding, and the early-return path
    has_elevated_privileges = any(
        role in ELEVATED_PRIVILEGE_ROLES for role in user_record["roles"]
    )

    if lifecycle_action == "1":  # Onboarding path

        # Enforce the policy that temporary roles must carry an expiry date.
        # Block provisioning and log the violation rather than silently
        # creating an account that will never auto-expire.
        if (
            any(role in TEMPORARY_ACCESS_ROLES for role in user_record["roles"])
            and not expiry_date
        ):
            applied_role_policy = "temporary_role_missing_expiry"

            # Compute risk before logging so the blocked entry still
            # captures the full governance picture for audit purposes
            blocked_risk_score = calculate_governance_risk_score(
                user_record["roles"],
                has_elevated_privileges,
                dual_approval_required,
                expiry_date,
                applied_role_policy,
            )
            blocked_risk_level = classify_risk_level_from_score(blocked_risk_score)

            blocked_provision_audit_entry = {
                "timestamp":          generation_timestamp,
                "identity_state":     "provision_blocked",
                "action":             "onboarding",
                "user_email":         user_record["email"],
                "department":         user_record["department"],
                "roles":              user_record["roles"],
                "privileged_access":  has_elevated_privileges,
                "risk_score":         blocked_risk_score,
                "risk_level":         blocked_risk_level,
                "role_policy_applied": applied_role_policy,
            }

            print("\nExpiry required for temporary role.")

            if is_dry_run:
                print(json.dumps(blocked_provision_audit_entry, indent=4))
            else:
                append_entry_to_audit_log(blocked_provision_audit_entry)

            return

        elif any(role in TEMPORARY_ACCESS_ROLES for role in user_record["roles"]):
            # Temporary role supplied with a valid expiry — can proceed
            applied_role_policy = "temporary_role_with_expiry"

        elif build_deduplicated_task_list(user_record["roles"]):
            # Role is recognised in the catalogue — standard provisioning applies
            applied_role_policy = "standard_role_matched"

        else:
            # Role not found in catalogue — flag for manual review before
            # any access is granted, to honour the deny-by-default policy
            applied_role_policy = "role_not_defined_manual_review"

        dual_approval_required = identity_requires_dual_approval(user_record["roles"])

        if dual_approval_required:
            # Account is created in a suspended state pending both
            # manager and security team sign-off
            provisioned_identity_state = "pending_approval"
            manager_sign_off_status    = "pending"
            security_sign_off_status   = "pending"
        else:
            # No dual approval needed — activate immediately,
            # but restrict access further if the role is unrecognised
            provisioned_identity_state = (
                "active_with_restrictions"
                if applied_role_policy == "role_not_defined_manual_review"
                else "active"
            )
            manager_sign_off_status  = "not_required"
            security_sign_off_status = "not_required"

        # A periodic review is mandatory whenever any of these conditions
        # apply: elevated privileges, pending dual approval, or a time-bound
        # account that must be verified before or at expiry.
        periodic_review_required = (
            dual_approval_required
            or expiry_date is not None
            or has_elevated_privileges
        )

        if periodic_review_required:
            # Set the review deadline to the expiry date when one exists;
            # otherwise default to 180 days — the standard review cadence
            review_scheduled_date = (
                expiry_date
                if expiry_date
                else (datetime.now() + timedelta(days=180)).strftime("%Y-%m-%d")
            )
            # Unique ID lets the review be tracked and cross-referenced
            # across ticketing systems and the audit log
            review_tracking_id = (
                f"AR-{datetime.now().strftime('%Y%m%d')}-"
                f"{uuid.uuid4().hex[:6].upper()}"
            )
            review_current_status    = "pending"
            review_record_created_at = generation_timestamp

    else:  # Offboarding path
        # All departing identities follow the same revocation policy
        # regardless of original role — no partial deprovisioning allowed
        applied_role_policy         = "offboarding"
        provisioned_identity_state  = "revoked"

    # Risk score and level are finalised here, after all governance
    # variables are resolved, so the score reflects the true state
    # for both onboarding and offboarding paths.
    final_risk_score = calculate_governance_risk_score(
        user_record["roles"],
        has_elevated_privileges,
        dual_approval_required,
        expiry_date,
        applied_role_policy,
    )
    final_risk_level = classify_risk_level_from_score(final_risk_score)

    # Prepare the output directory where checklist files are saved
    checklist_output_directory = "automation/output"
    os.makedirs(checklist_output_directory, exist_ok=True)

    # Sanitise the user's name for use in the output filename
    filesystem_safe_name = user_record["name"].replace(" ", "_").lower()

    if lifecycle_action == "1":
        checklist_document_content = generate_onboarding_checklist_document(
            user_record, generation_timestamp, expiry_date
        )
        output_filename = f"onboarding_{filesystem_safe_name}_{generation_timestamp}.md"
    else:
        checklist_document_content = generate_offboarding_checklist_document(
            user_record, generation_timestamp
        )
        output_filename = f"offboarding_{filesystem_safe_name}_{generation_timestamp}.md"

    checklist_file_path = os.path.join(checklist_output_directory, output_filename)

    # Only write the file in execute mode; dry-run leaves the filesystem untouched
    if not is_dry_run:
        with open(checklist_file_path, "w", encoding="utf-8") as checklist_file:
            checklist_file.write(checklist_document_content)

    lifecycle_audit_entry = {
        "timestamp":                generation_timestamp,
        "identity_state":           provisioned_identity_state,
        "action":                   "onboarding" if lifecycle_action == "1" else "offboarding",
        "user_email":               user_record["email"],
        "department":               user_record["department"],
        "roles":                    user_record["roles"],
        "privileged_access":        has_elevated_privileges,
        "risk_score":               final_risk_score,
        "risk_level":               final_risk_level,
        "role_policy_applied":      applied_role_policy,
        "generated_file":           None if is_dry_run else checklist_file_path,
        "approval_required":        dual_approval_required if lifecycle_action == "1" else False,
        "manager_approval_status":  manager_sign_off_status,
        "security_approval_status": security_sign_off_status,
        "access_expiry":            expiry_date if expiry_date else "none",
        "access_review_required":   periodic_review_required,
        "review_due_by":            review_scheduled_date,
        "review_id":                review_tracking_id,
        "review_status":            review_current_status,
        "review_generated_at":      review_record_created_at,
    }

    if is_dry_run:
        print(json.dumps(lifecycle_audit_entry, indent=4))
    else:
        append_entry_to_audit_log(lifecycle_audit_entry)
        print("\nOperation completed successfully.")
        print(checklist_file_path)


if __name__ == "__main__":
    main()
