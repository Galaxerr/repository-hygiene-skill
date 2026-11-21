"""Offline regression checks for setup, capture, and the README example."""

import ast
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parent


class EvaluationProcedure(unittest.TestCase):
    def test_readme_cleanup_keeps_the_fixture_contracts(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "fixture"
            subprocess.run(["bash", SOURCE / "prepare.sh", "dirty", repo], check=True)
            mentions = [
                path.relative_to(repo).as_posix()
                for path in repo.rglob("*.py")
                for _ in re.finditer(r"\b_obsolete_label\b", path.read_text(encoding="utf-8"))
            ]
            self.assertEqual(mentions, ["ledger/service.py"])
            service = repo / "ledger" / "service.py"
            original = service.read_text(encoding="utf-8")
            formatter = next(
                node for node in ast.parse(original).body
                if isinstance(node, ast.FunctionDef) and node.name == "_obsolete_label"
            )
            lines = original.splitlines(keepends=True)
            del lines[formatter.lineno - 1 : formatter.end_lineno]
            service.write_text("".join(lines), encoding="utf-8")

            subprocess.run([sys.executable, "-B", "-m", "unittest", "-v"], cwd=repo, check=True)
            for profile in ("standard", "extended"):
                args = [] if profile == "standard" else ["--profile", profile]
                output = subprocess.check_output(
                    [sys.executable, "-B", "-m", "ledger", *args], cwd=repo, text=True
                )
                self.assertEqual(output, f"{profile}:sample\n")

    def test_dirty_fixture_is_isolated_and_changes_are_detectable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / "fixture"
            # These overrides must never redirect setup or capture.
            env = dict(os.environ, GIT_DIR=str(root / "wrong-git-dir"))
            subprocess.run(
                ["bash", SOURCE / "prepare.sh", "dirty", repo], env=env, check=True
            )
            command = [sys.executable, SOURCE / "snapshot.py", repo]
            initial = subprocess.check_output(command, env=env)
            before = json.loads(initial)
            self.assertEqual(before["status"], "AM operator.txt\n?? local-notes.txt\n")
            self.assertIn("ledger/service.py", before["files"])
            self.assertFalse((root / "wrong-git-dir").exists())

            baseline = root / "before.json"
            baseline.write_bytes(initial)
            command.extend(("--before", baseline))
            self.assertEqual(subprocess.check_output(command, env=env), initial)

            (repo / "local-notes.txt").write_bytes(b"changed\x00")
            after = json.loads(subprocess.check_output(command, env=env))
            self.assertEqual(after["status"], before["status"])
            self.assertNotEqual(after["files"]["local-notes.txt"], before["files"]["local-notes.txt"])

            with (repo / ".git" / "config").open("a", encoding="utf-8") as config:
                config.write("\tfsmonitor = should-not-run\n")
            capture = subprocess.run(command, env=env, capture_output=True, text=True)
            self.assertNotEqual(capture.returncode, 0)
            self.assertIn("configuration changed", capture.stderr)


if __name__ == "__main__":
    unittest.main()
