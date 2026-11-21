"""Offline regression checks for setup and capture."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parent


class EvaluationProcedure(unittest.TestCase):
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
