#!/usr/bin/env python3
"""Validate GitHub Actions workflow syntax and remote action references."""

from __future__ import annotations

import argparse
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import yaml

USES_RE = re.compile(r"^\s*(?:-\s*)?uses:\s*[\"']?([^\"'#\s]+)")
SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")


@dataclass(frozen=True)
class ActionUse:
    repository: str
    ref: str
    workflow: Path
    line: int


def collect_action_uses(workflow_dir: Path) -> list[ActionUse]:
    workflow_paths = sorted(
        set(workflow_dir.glob("*.yml")) | set(workflow_dir.glob("*.yaml"))
    )
    if not workflow_paths:
        raise ValueError(f"No workflow files found in {workflow_dir}")

    action_uses: list[ActionUse] = []
    errors: list[str] = []

    for workflow_path in workflow_paths:
        text = workflow_path.read_text(encoding="utf-8")
        try:
            yaml.safe_load(text)
        except yaml.YAMLError as exc:
            errors.append(f"{workflow_path}: invalid YAML: {exc}")
            continue

        for line_number, line in enumerate(text.splitlines(), start=1):
            match = USES_RE.match(line)
            if not match:
                continue

            action = match.group(1)
            if action.startswith(("./", "docker://")):
                continue
            if "@" not in action:
                errors.append(
                    f"{workflow_path}:{line_number}: remote action has no ref: {action}"
                )
                continue

            location, ref = action.rsplit("@", 1)
            location_parts = location.split("/")
            if len(location_parts) < 2 or not ref:
                errors.append(
                    f"{workflow_path}:{line_number}: invalid remote action: {action}"
                )
                continue

            action_uses.append(
                ActionUse(
                    repository="/".join(location_parts[:2]),
                    ref=ref,
                    workflow=workflow_path,
                    line=line_number,
                )
            )

    if errors:
        raise ValueError("\n".join(errors))
    return action_uses


def github_page_exists(page_path: str, attempts: int = 3) -> bool:
    url = f"https://github.com{page_path}"
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "text/html",
            "User-Agent": "mdstyledocx-pre-push",
        },
    )

    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                return response.status == 200
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return False
            if exc.code < 500 and exc.code != 429:
                raise RuntimeError(
                    f"GitHub returned HTTP {exc.code} for {page_path}"
                ) from exc
            error: Exception = exc
        except (TimeoutError, urllib.error.URLError) as exc:
            error = exc

        if attempt + 1 < attempts:
            time.sleep(2**attempt)

    raise RuntimeError(
        f"Unable to query GitHub for {page_path} after {attempts} attempts: "
        f"{error}"
    )


def action_ref_exists(repository: str, ref: str) -> bool:
    repository_path = urllib.parse.quote(repository, safe="/")
    if SHA_RE.fullmatch(ref):
        commit = urllib.parse.quote(ref, safe="")
        return github_page_exists(f"/{repository_path}/commit/{commit}")

    for prefix in ("refs/heads/", "refs/tags/"):
        if ref.startswith(prefix):
            ref = ref.removeprefix(prefix)
            break

    ref_path = urllib.parse.quote(ref, safe="")
    return github_page_exists(f"/{repository_path}/tree/{ref_path}")


def validate_action_uses(action_uses: list[ActionUse]) -> None:
    failures: list[str] = []
    checked_actions: dict[tuple[str, str], bool] = {}

    for action_use in action_uses:
        action_key = (action_use.repository, action_use.ref)
        if action_key not in checked_actions:
            checked_actions[action_key] = action_ref_exists(
                action_use.repository, action_use.ref
            )
        if not checked_actions[action_key]:
            failures.append(
                f"{action_use.workflow}:{action_use.line}: "
                f"{action_use.repository}@{action_use.ref} does not resolve to a "
                "GitHub branch, tag, or commit"
            )

    if failures:
        raise ValueError("\n".join(failures))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--workflow-dir", type=Path, default=Path(".github/workflows")
    )
    args = parser.parse_args()

    try:
        action_uses = collect_action_uses(args.workflow_dir)
        validate_action_uses(action_uses)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"GitHub Actions preflight failed:\n{exc}", file=sys.stderr)
        return 1

    unique_actions = {(item.repository, item.ref) for item in action_uses}
    print(
        f"GitHub Actions preflight passed: {len(unique_actions)} unique remote "
        f"action references across {len({item.workflow for item in action_uses})} "
        "workflow files."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
