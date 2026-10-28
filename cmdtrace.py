
#!/usr/bin/env python3

import argparse
import re
import shlex
from dataclasses import dataclass


@dataclass
class ImpactReport:
    command: str
    action: str
    target: str
    risk: str
    warning: str
    execution: str = "Not performed."
    notes: str = ""

    def display(self):
        lines = [
            "=== cmdtrace: Command Impact Report ===",
            f"Command:   {self.command}",
            f"Action:    {self.action}",
            f"Target:    {self.target}",
            f"Risk:      {self.risk}",
            f"Warning:   {self.warning}",
        ]

        if self.notes:
            lines.append(f"Notes:     {self.notes}")

        lines.append(f"Execution: {self.execution}")
        return "\n".join(lines)


def analyze(command_text):
    original = command_text.strip()

    if not original:
        return ImpactReport(
            original, "No command provided", "(none)", "UNKNOWN",
            "Enter a command to analyze."
        )

    # Detect shell operators and complex syntax.
    if re.search(r"(\|\||&&|[|;&<>`]|\$\(|\$\{|\n)", original):
        return ImpactReport(
            original,
            "Complex shell syntax detected",
            "(requires deeper analysis)",
            "UNKNOWN",
            "Pipes, redirection, chaining, or command substitution "
            "cannot be fully analyzed by this prototype.",
            notes="Analyze individual simple commands separately."
        )

    # Variable values cannot be predicted without evaluating the environment.
    if re.search(r"\$(?:[A-Za-z_][A-Za-z0-9_]*|\{[^}]+\})", original):
        return ImpactReport(
            original,
            "Command contains variable expansion",
            "(variable-dependent)",
            "UNKNOWN",
            "Variable values are not expanded, so the final target "
            "may be different.",
            notes="No command was executed."
        )

    try:
        tokens = shlex.split(original)
    except ValueError:
        return ImpactReport(
            original, "Could not parse command", "(unknown)", "UNKNOWN",
            "Check for unmatched quotation marks."
        )

    if not tokens:
        return ImpactReport(
            original, "No command provided", "(none)", "UNKNOWN",
            "Enter a command to analyze."
        )

    command = tokens[0]
    args = tokens[1:]
    targets = [arg for arg in args if not arg.startswith("-")]
    target = ", ".join(targets) if targets else "(not specified)"

    def report(action, risk, warning, report_target=target):
        return ImpactReport(
            original, action, report_target, risk, warning
        )

    # Read-only and information commands.
    simple_commands = {
        "pwd": ("Display current directory", "Prints the current directory."),
        "whoami": ("Display current user", "Displays the current username."),
        "date": ("Display date and time", "Displays the system date and time."),
        "hostname": ("Display host name", "Displays the computer's host name."),
        "uname": ("Display system information", "Displays operating-system information."),
        "ls": ("List directory contents", "Lists files and directories."),
        "cat": ("Read file contents", "Displays file contents; sensitive data may be exposed."),
        "head": ("Read beginning of a file", "Displays the beginning of a file."),
        "tail": ("Read end of a file", "Displays the end of a file."),
        "less": ("View file contents", "Displays file contents for browsing."),
        "more": ("View file contents", "Displays file contents for browsing."),
        "wc": ("Count lines, words, or bytes", "Counts content in the specified input."),
        "grep": ("Search text", "Searches input for matching text."),
        "file": ("Identify file type", "Reports the type of a file."),
        "stat": ("Display file information", "Displays file metadata."),
    }

    if command in simple_commands:
        action, warning = simple_commands[command]
        return report(action, "LOW", warning)

    # File and directory removal.
    if command == "rm":
        if not targets:
            return report(
                "Remove files or directories", "UNKNOWN",
                "No clear target was identified."
            )

        recursive = any(
            flag in args for flag in
            ["-r", "-R", "-rf", "-fr", "--recursive"]
        )
        force = any(
            flag in args for flag in
            ["-f", "-rf", "-fr", "--force"]
        )

        if recursive or force:
            risk = "HIGH"
            warning = "May delete data recursively or without prompting."
        else:
            risk = "MEDIUM"
            warning = "Deletes the specified item; recovery may be difficult."

        if any(path in targets for path in ["/", ".", ".."]):
            risk = "HIGH"
            warning = "A broad or special path was detected. Review the target carefully."

        return report("Remove files or directories", risk, warning)

    # Move and copy.
    if command == "mv":
        if len(targets) < 2:
            return report(
                "Move or rename files", "MEDIUM",
                "Check that both source and destination are provided."
            )

        if "-f" in args or "--force" in args:
            return report(
                "Move or rename files", "HIGH",
                "The force option may overwrite destination files."
            )

        return report(
            "Move or rename files", "MEDIUM",
            "Files may be moved or an existing destination may be overwritten."
        )

    if command == "cp":
        if len(targets) < 2:
            return report(
                "Copy files or directories", "MEDIUM",
                "Check that both source and destination are provided."
            )

        risk = "HIGH" if any(
            flag in args for flag in ["-f", "--force"]
        ) else "MEDIUM"

        return report(
            "Copy files or directories", risk,
            "Files may be copied and existing destinations may be overwritten."
        )

    # Directory and file creation.
    if command == "mkdir":
        return report(
            "Create directories", "LOW",
            "Creates directories; permissions or existing paths may cause errors."
        )

    if command == "touch":
        return report(
            "Create files or update timestamps", "LOW",
            "May create an empty file or update file timestamps."
        )

    # Permissions and ownership.
    if command == "chmod":
        if any(flag in args for flag in ["-R", "--recursive"]):
            return report(
                "Change file permissions", "HIGH",
                "Recursive permission changes can affect many files."
            )

        if any(mode in args for mode in ["777", "a+rwx"]):
            return report(
                "Change file permissions", "HIGH",
                "Broad permissions may allow unintended access."
            )

        return report(
            "Change file permissions", "MEDIUM",
            "Verify the permission mode and target."
        )

    if command == "chown":
        return report(
            "Change file ownership", "HIGH",
            "Ownership changes can affect access and service behavior."
        )

    # Find can perform actions as well as search.
    if command == "find":
        action_flags = ["-delete", "-exec", "-execdir", "-ok", "-okdir"]

        if any(flag in args for flag in action_flags):
            return report(
                "Search files with an action option", "HIGH",
                "The find expression may modify files or execute another command."
            )

        return report(
            "Search for files and directories", "LOW",
            "Searches for files matching the specified conditions."
        )

    # Elevated privileges.
    if command == "sudo":
        if not args:
            return report(
                "Run a command with elevated privileges", "HIGH",
                "No command was supplied after sudo."
            )

        nested = analyze(" ".join(shlex.quote(arg) for arg in args))

        return ImpactReport(
            original,
            "Elevated privileges: " + nested.action,
            nested.target,
            "HIGH" if nested.risk != "UNKNOWN" else "UNKNOWN",
            "Elevated privileges can increase the impact. " + nested.warning,
            notes="Review the complete command before using sudo."
        )

    if command in ["kill", "killall", "pkill"]:
        return report(
            "Send a signal to process(es)", "HIGH",
            "May terminate processes or disrupt services."
        )

    # Package management.
    if command in ["apt", "apt-get", "brew", "pip", "pip3"]:
        subcommand = args[0] if args else ""

        if subcommand in ["remove", "purge", "uninstall", "autoremove"]:
            return report(
                "Remove installed software or packages", "HIGH",
                "May uninstall software or dependencies."
            )

        if subcommand in ["install", "upgrade", "update"]:
            return report(
                "Manage software packages", "MEDIUM",
                "May download, install, or change software and dependencies."
            )

        return report(
            "Manage software packages", "MEDIUM",
            "Review the package-manager subcommand and its effects."
        )

    # Network tools.
    if command in ["curl", "wget"]:
        return report(
            "Transfer data over a network", "MEDIUM",
            "May contact a remote server or download data. Verify the URL and options."
        )

    return report(
        "Unknown or unsupported command", "UNKNOWN",
        "No matching rule is available. The impact cannot be reliably predicted."
    )


def main():
    parser = argparse.ArgumentParser(
        description="Predict the likely impact of a shell command without executing it."
    )
    parser.add_argument(
        "command", nargs="*",
        help="Command to analyze, enclosed in quotation marks"
    )
    parser.add_argument(
        "--version", action="version", version="cmdtrace 0.2.0"
    )

    args = parser.parse_args()
    command_text = " ".join(args.command)

    if not command_text:
        parser.print_help()
        return

    print(analyze(command_text).display())


if __name__ == "__main__":
    main()
