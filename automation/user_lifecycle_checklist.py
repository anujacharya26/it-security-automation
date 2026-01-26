# user_lifecycle_checklist.py
# Automation-assisted user onboarding and offboarding checklist
# Purpose: Reduce human error and standardize IT & security operations

def get_user_details():
    print("\nEnter user details:")
    name = input("Employee Name: ")
    email = input("Email Address: ")
    department = input("Department: ")
    role = input("Role: ")
    manager = input("Manager Name: ")
    date = input("Start Date / Last Working Day: ")

    return {
        "name": name,
        "email": email,
        "department": department,
        "role": role,
        "manager": manager,
        "date": date
    }


def onboarding_checklist(user):
    return f"""
# 🧑‍💼 User Onboarding Checklist

**Name:** {user['name']}
**Email:** {user['email']}
**Department:** {user['department']}
**Role:** {user['role']}
**Manager:** {user['manager']}
**Start Date:** {user['date']}

## ✅ IT & Security Tasks
- [ ] Create identity account
- [ ] Assign role-based access groups
- [ ] Enable MFA
- [ ] Provision email and collaboration tools
- [ ] Assign device (laptop)
- [ ] Apply security baseline
- [ ] Notify manager of completion
"""


def offboarding_checklist(user):
    return f"""
# 🚫 User Offboarding Checklist

**Name:** {user['name']}
**Email:** {user['email']}
**Department:** {user['department']}
**Role:** {user['role']}
**Manager:** {user['manager']}
**Last Working Day:** {user['date']}

## 🔐 IT & Security Tasks
- [ ] Disable identity account
- [ ] Remove from access groups
- [ ] Revoke active sessions
- [ ] Collect company devices
- [ ] Archive user data if required
- [ ] Rotate shared credentials (if any)
- [ ] Log offboarding completion
"""


def main():
    print("User Lifecycle Automation Tool")
    print("1. Onboarding")
    print("2. Offboarding")

    choice = input("Select an option (1 or 2): ")

    user = get_user_details()

    if choice == "1":
        checklist = onboarding_checklist(user)
        filename = f"onboarding_{user['name'].replace(' ', '_')}.md"
    elif choice == "2":
        checklist = offboarding_checklist(user)
        filename = f"offboarding_{user['name'].replace(' ', '_')}.md"
    else:
        print("Invalid option selected.")
        return

    with open(filename, "w") as file:
        file.write(checklist)

    print(f"\nChecklist created successfully: {filename}")


if __name__ == "__main__":
    main()
