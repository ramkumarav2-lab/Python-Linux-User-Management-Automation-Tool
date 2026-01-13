"""
Linux User Management Automation Script
=======================================

Author: Ramkumar V
Email: ramkumarav2@gmail.com
Version: 1.0.0
Date: 2025-11-29

Description:
- Python-based automation tool to manage Linux users via Ansible
- Dynamically generates Ansible playbooks
- Create / Modify / Delete users
- Supports sudo access & password expiry policies
"""

__author__ = "Ramkumar V"
__version__ = "1.0.0"

import yaml
import subprocess

# Vault file path
vault_file = "vault.yml"


# --------------------------------------------------
# Read user details (Create / Modify)
# --------------------------------------------------
def read_user():
    users = []
    user_count = int(input("Enter how many users needs to be created: ").strip())

    for i in range(user_count):
        print("\n" + "*" * 90)
        print(f"### User {i + 1} Details ###")
        print("\n" + "*" * 90 + "\n")

        username = input("1. Enter the username: ").strip()
        state = input("2. Enter state (present/absent): ").strip()
        comment = input("3. Enter comment (optional): ").strip()
        shell = input("4. Enter shell (optional): ").strip()
        group = input("5. Enter group (optional): ").strip()
        groups = input("6. Enter groups (optional): ").strip()
        password = input("7. Enter password (optional): ").strip()

        print(
            "\nChoose an option:\n"
            "1 - Force password change on first login\n"
            "2 - Set maximum password expiry days\n"
            "3 - Not required\n"
        )

        change = input("Enter your choice (1 / 2 / 3): ").strip()
        change_max = None

        if change == "2":
            change_max = input("Enter maximum days of expiry: ").strip()

        sudo = input("\n8. Should user have sudo access? (yes/no): ").strip().lower() == "yes"

        users.append({
            "username": username,
            "state": state,
            "comment": comment if comment else None,
            "shell": shell if shell else None,
            "group": group if group else None,
            "groups": groups if groups else None,
            "password": password if password else None,
            "change": change if change else None,
            "change_max": change_max if change_max else None,
            "sudo": sudo
        })

    return users


# --------------------------------------------------
# Read users for deletion
# --------------------------------------------------
def read_user_delete():
    users_delete = []
    user_count = int(input("Enter how many users needs to be deleted: ").strip())

    for i in range(user_count):
        print("\n" + "*" * 90)
        print(f"### User {i + 1} Details ###")
        print("\n" + "*" * 90 + "\n")

        username = input("1. Enter the username: ").strip()

        users_delete.append({
            "username": username
        })

    return users_delete


# --------------------------------------------------
# Generate Ansible playbook (Create / Modify)
# --------------------------------------------------
def generate_playbook(users):
    tasks = []

    for user in users:
        if user.get("password") is None:
            task = {
                "name": f"Manage user {user['username']}",
                "ansible.builtin.user": {
                    "name": user["username"],
                    "state": user["state"]
                }
            }
        else:
            task = {
                "name": f"Manage user {user['username']}",
                "ansible.builtin.user": {
                    "name": user["username"],
                    "state": user["state"],
                    "password": "{{ '" + user["password"] + "' | password_hash('sha512') }}"
                }
            }

        # Optional attributes
        if user.get("comment"):
            task["ansible.builtin.user"]["comment"] = user["comment"]

        if user.get("shell"):
            task["ansible.builtin.user"]["shell"] = user["shell"]

        if user.get("group"):
            task["ansible.builtin.user"]["group"] = user["group"]

        if user.get("groups"):
            task["ansible.builtin.user"]["groups"] = user["groups"]

        tasks.append(task)

        # Password expiry
        if user.get("change") != "3":
            if user.get("change") == "2":
                change_task = {
                    "name": f"Set password expiry (maximum days) for {user['username']}",
                    "ansible.builtin.command": {
                        "cmd": f"chage -M {user['change_max']} {user['username']}"
                    }
                }
                tasks.append(change_task)

            elif user.get("change") == "1":
                change_task = {
                    "name": f"Force password change on first login for {user['username']}",
                    "ansible.builtin.command": {
                        "cmd": f"chage -d 0 {user['username']}"
                    }
                }
                tasks.append(change_task)

        # Sudo access
        if user.get("sudo"):
            sudo_task = {
                "name": f"Add {user['username']} to sudoers",
                "ansible.builtin.lineinfile": {
                    "path": "/etc/sudoers",
                    "state": "present",
                    "regexp": f"^{user['username']}",
                    "line": f"{user['username']} ALL=(ALL) NOPASSWD:ALL",
                    "validate": "visudo -cf %s"
                }
            }
            tasks.append(sudo_task)

    playbook = [{
        "name": "User Management Workflow",
        "hosts": "all",
        "become": True,
        "tasks": tasks
    }]

    return playbook


# --------------------------------------------------
# Generate Ansible playbook (Delete)
# --------------------------------------------------
def generate_playbook_delete(users_delete):
    tasks = []

    for user in users_delete:
        task = {
            "name": f"Remove user {user['username']}",
            "ansible.builtin.user": {
                "name": user["username"],
                "state": "absent",
                "remove": "yes"
            }
        }
        tasks.append(task)

    playbook = [{
        "name": "User Management Workflow",
        "hosts": "all",
        "become": True,
        "tasks": tasks
    }]

    return playbook


# --------------------------------------------------
# Write playbook to YAML
# --------------------------------------------------
def write_playbook(playbook, filename="user_management.yml"):
    yaml_text = yaml.dump(playbook, default_flow_style=False)
    yaml_text = yaml_text.replace("\n- name:", "\n\n- name:")

    with open(filename, "w") as f:
        f.write(yaml_text)

    print(f"Playbook generated: {filename}")
    return filename


# --------------------------------------------------
# Execute playbook
# --------------------------------------------------
def run_playbook(filename):
    print("Executing playbook...")
    subprocess.run([
        "ansible-playbook",
        filename,
        "--extra-vars",
        f"@{vault_file}",
        "--ask-vault-pass"
    ])


# --------------------------------------------------
# Main
# --------------------------------------------------
if __name__ == "__main__":
    print("\n" + "#" * 90)
    print("#" + " " * 30 + "Redhat User Management" + " " * 36 + "#")
    print("#" * 90 + "\n")

    option = input("Do you want to run existing playbook (yes/no): ").strip()

    if option == "yes":
        run_playbook("user_management.yml")

    elif option == "no":
        print(
            "\nPlease choose an action:\n"
            "1 → Create/Modify a new user\n"
            "2 → Delete an existing user\n"
        )

        cr_option = input("Enter your choice [1/2]: ").strip()

        if cr_option == "1":
            users = read_user()
            playbook = generate_playbook(users)
            filename = write_playbook(playbook)
            run_playbook(filename)

        elif cr_option == "2":
            delete_confirm = input("You are deleting a user (yes/no): ").strip()
            if delete_confirm == "yes":
                users_delete = read_user_delete()
                playbook = generate_playbook_delete(users_delete)
                filename = write_playbook(playbook)
                run_playbook(filename)
            else:
                print("Exiting...")

        else:
            print("Exiting...")

    else:
        print("Exiting...")
