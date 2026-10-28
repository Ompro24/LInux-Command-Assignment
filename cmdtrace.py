
import argparse
import shlex


def analyze_command(command):
    try:
        parts = shlex.split(command)
    except ValueError:
        return {
            "action": "Unable to parse command",
            "target": "Unknown",
            "risk": "UNKNOWN",
            "warning": "Check the command's quotation marks."
        }

    if not parts:
        return {
            "action": "No command provided",
            "target": "None",
            "risk": "UNKNOWN",
            "warning": "Enter a command to analyze."
        }

    name = parts[0]
    args = parts[1:]

    # Remove ordinary command options to identify likely targets.
    targets = [
        arg for arg in args
        if not arg.startswith("-")
    ]

    if name == "rm":
        action = "Delete files or directories"
        target = ", ".join(targets) if targets else "Unclear"
        risk = "HIGH"
        warning = "Deletion may be difficult or impossible to undo."

    elif name == "mv":
        action = "Move or rename files"
        target = ", ".join(targets) if targets else "Unclear"
        risk = "MEDIUM"
        warning = "Files may be moved or overwritten."

    elif name == "cp":
        action = "Copy files"
        target = ", ".join(targets) if targets else "Unclear"
        risk = "MEDIUM"
        warning = "Existing files may be overwritten."

    elif name in ("pwd", "ls"):
        action = "Inspect the current directory or its contents"
        target = ", ".join(targets) if targets else "Current directory"
        risk = "LOW"
        warning = "No file changes are expected from this command."

    else:
        action = "Command not supported yet"
        target = ", ".join(targets) if targets else "Unknown"
        risk = "UNKNOWN"
        warning = "The command was not analyzed. Do not assume it is safe."

    return {
        "action": action,
        "target": target,
        "risk": risk,
        "warning": warning
    }


def main():
    parser = argparse.ArgumentParser(
        description="Analyze a command without executing it."
    )
    parser.add_argument(
        "command",
        help="Shell command to inspect, enclosed in quotes"
    )

    args = parser.parse_args()
    report = analyze_command(args.command)

    print("\n=== cmdtrace: Command Impact Report ===")
    print(f"Command: {args.command}")
    print(f"Action:  {report['action']}")
    print(f"Target:  {report['target']}")
    print(f"Risk:    {report['risk']}")
    print(f"Warning: {report['warning']}")
    print("Execution: Not performed.")


if __name__ == "__main__":
    main()
