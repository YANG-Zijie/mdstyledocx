from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "check_action_refs.py"
SPEC = importlib.util.spec_from_file_location("check_action_refs", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
check_action_refs = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = check_action_refs
SPEC.loader.exec_module(check_action_refs)


class ActionReferenceTests(unittest.TestCase):
    def test_collects_remote_actions_and_ignores_local_or_docker_actions(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            workflow_directory = Path(temporary_directory)
            (workflow_directory / "ci.yml").write_text(
                """
name: CI
on: push
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: owner/action/subdirectory@0123456789abcdef0123456789abcdef01234567
      - uses: ./local-action
      - uses: docker://alpine:3.20
""",
                encoding="utf-8",
            )

            action_uses = check_action_refs.collect_action_uses(workflow_directory)

        self.assertEqual(
            [(item.repository, item.ref) for item in action_uses],
            [
                ("actions/checkout", "v6"),
                (
                    "owner/action",
                    "0123456789abcdef0123456789abcdef01234567",
                ),
            ],
        )

    def test_resolves_tags_branches_and_commits_with_github_page_paths(self):
        requested_paths = []

        def fake_page_exists(page_path, attempts=3):
            requested_paths.append(page_path)
            return page_path.endswith(("/tree/v1", "/tree/main", "/" + "c" * 40))

        original_page_exists = check_action_refs.github_page_exists
        check_action_refs.github_page_exists = fake_page_exists
        try:
            self.assertTrue(
                check_action_refs.action_ref_exists("owner/action", "v1")
            )
            self.assertTrue(
                check_action_refs.action_ref_exists("owner/action", "main")
            )
            self.assertTrue(
                check_action_refs.action_ref_exists("owner/action", "c" * 40)
            )
            self.assertFalse(
                check_action_refs.action_ref_exists("owner/action", "v9")
            )
        finally:
            check_action_refs.github_page_exists = original_page_exists

        self.assertIn("/owner/action/tree/v9", requested_paths)

    def test_rejects_remote_action_without_ref(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            workflow_directory = Path(temporary_directory)
            (workflow_directory / "ci.yml").write_text(
                """
name: CI
on: push
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout
""",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "has no ref"):
                check_action_refs.collect_action_uses(workflow_directory)
