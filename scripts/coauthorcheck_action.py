#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


COMMENT_MARKER = "<!-- coauthorcheck-comment -->"


def as_bool(value: str) -> bool:
    return value.strip().lower() == "true"


def set_output(name: str, value: str) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        return
    with open(output_path, "a", encoding="utf-8") as handle:
        handle.write(f"{name}={value}\n")


def format_issue(issue: dict[str, object]) -> str:
    pieces: list[str] = []
    line_number = issue.get("line_number")
    if isinstance(line_number, int):
        pieces.append(f"line {line_number}:")
    code = str(issue.get("code") or "unknown")
    message = str(issue.get("message") or "Validation issue.")
    pieces.append(f"[{code}] {message}")
    bullet = f"- {' '.join(pieces)}"
    suggestion = issue.get("suggestion")
    if suggestion:
        bullet += f"\n  Suggestion: `{suggestion}`"
    return bullet


def render_log_text(payload: dict[str, object]) -> str:
    summary = payload.get("summary") or {}
    issue_count = int(summary.get("issue_count") or 0)
    invalid_commit_count = int(summary.get("invalid_commit_count") or 0)
    warning_count = int(summary.get("warning_count") or 0)
    status = str(payload.get("status") or "error")

    lines: list[str] = []
    if status == "pass":
        if warning_count > 0:
            lines.append(
                f"coauthorcheck passed with {warning_count} warning(s) across {int(summary.get('warning_commit_count') or 0)} commit(s)."
            )
        else:
            lines.append("coauthorcheck passed with no issues.")
    elif status == "fail":
        lines.append(f"coauthorcheck found {issue_count} issue(s) across {invalid_commit_count} commit(s).")
    else:
        error = payload.get("error") or {}
        lines.append(str(error.get("message") or "coauthorcheck failed to run."))
        hint = error.get("hint")
        if hint:
            lines.append(f"Hint: {hint}")

    for result in payload.get("results") or []:
        if not isinstance(result, dict):
            continue
        issues = [issue for issue in (result.get("issues") or []) if isinstance(issue, dict)]
        if not issues:
            continue
        lines.append("")
        lines.append(f"{result.get('source') or 'unknown'}")
        for issue in issues:
            lines.append(format_issue(issue))

    return "\n".join(lines).rstrip() + ("\n" if lines else "")


def render_comment(header: str, payload: dict[str, object]) -> str:
    summary = payload.get("summary") or {}
    issue_count = int(summary.get("issue_count") or 0)
    invalid_commit_count = int(summary.get("invalid_commit_count") or 0)
    warning_count = int(summary.get("warning_count") or 0)
    warning_commit_count = int(summary.get("warning_commit_count") or 0)
    status = str(payload.get("status") or "error")

    lines = [COMMENT_MARKER, f"## {header}", ""]
    if status == "pass":
        if warning_count > 0:
            lines.append(
                f"Validation passed with {warning_count} warning(s) across {warning_commit_count} commit(s)."
            )
        else:
            lines.append("Validation passed with no issues.")
    elif status == "fail":
        lines.append(f"Found {issue_count} issue(s) across {invalid_commit_count} commit(s).")
    else:
        error = payload.get("error") or {}
        message = str(error.get("message") or "coauthorcheck failed to run.")
        hint = error.get("hint")
        lines.append(message)
        if hint:
            lines.append("")
            lines.append(f"Hint: {hint}")

    grouped: list[tuple[str, list[dict[str, object]]]] = []
    for result in payload.get("results") or []:
        if not isinstance(result, dict):
            continue
        issues = [issue for issue in (result.get("issues") or []) if isinstance(issue, dict)]
        if not issues:
            continue
        source = str(result.get("source") or "unknown")
        grouped.append((source, issues))

    if grouped:
        lines.append("")
        for source, issues in grouped:
            lines.append(f"### {source}")
            for issue in issues:
                lines.append(format_issue(issue))
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    range_value = os.environ["INPUT_RANGE"]
    config = os.environ.get("INPUT_CONFIG", "").strip()
    requested_format = os.environ.get("INPUT_FORMAT", "text").strip() or "text"
    comment_on_pr = as_bool(os.environ.get("INPUT_COMMENT_ON_PR", "false"))
    comment_mode = os.environ.get("INPUT_COMMENT_MODE", "failures-only").strip() or "failures-only"
    delete_comment_on_success = as_bool(os.environ.get("INPUT_DELETE_COMMENT_ON_SUCCESS", "true"))
    comment_header = os.environ.get("INPUT_COMMENT_HEADER", "").strip() or "coauthorcheck"

    command = ["coauthorcheck", "--format", "json"]
    if config:
        command.extend(["--config", config])
    command.append(range_value)

    print(f"Running: {' '.join(command)}", file=sys.stderr)
    completed = subprocess.run(command, capture_output=True, text=True, check=False)

    raw_exit_code = completed.returncode
    exit_code = raw_exit_code if raw_exit_code in (0, 1, 2) else 2
    status = {0: "pass", 1: "fail", 2: "error"}[exit_code]
    issue_count = 0
    invalid_commit_count = 0
    warning_count = 0
    comment_intent = "none"
    comment_body_path = ""

    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)

    try:
        payload = json.loads(completed.stdout or "{}")
    except json.JSONDecodeError as exc:
        print(f"Failed to parse coauthorcheck JSON output: {exc}", file=sys.stderr)
        exit_code = 2
        status = "error"
        payload = {
            "status": "error",
            "error": {
                "message": "Failed to parse JSON output from coauthorcheck.",
                "hint": "Ensure the installed coauthorcheck version supports --format json.",
            },
        }

    summary = payload.get("summary") if isinstance(payload, dict) else {}
    if not isinstance(summary, dict):
        summary = {}
    issue_count = int(summary.get("issue_count") or 0)
    invalid_commit_count = int(summary.get("invalid_commit_count") or 0)
    warning_count = int(summary.get("warning_count") or 0)
    payload["status"] = status

    if requested_format == "json":
        print(json.dumps(payload, indent=2))
    else:
        log_text = render_log_text(payload)
        if log_text:
            print(log_text, end="")

    if comment_on_pr:
        if exit_code == 1:
            comment_intent = "upsert"
        elif exit_code == 0 and comment_mode == "always":
            comment_intent = "upsert"
        elif exit_code == 0 and delete_comment_on_success:
            comment_intent = "delete"

        if comment_intent == "upsert":
            comment_body = render_comment(comment_header, payload)
            temp_dir = Path(os.environ.get("RUNNER_TEMP", "."))
            comment_body_path = str(temp_dir / "coauthorcheck-comment.md")
            Path(comment_body_path).write_text(comment_body, encoding="utf-8")

    set_output("status", status)
    set_output("exit-code", str(exit_code))
    set_output("issue-count", str(issue_count))
    set_output("invalid-commit-count", str(invalid_commit_count))
    set_output("warning-count", str(warning_count))
    set_output("comment-intent", comment_intent)
    set_output("comment-body-path", comment_body_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
