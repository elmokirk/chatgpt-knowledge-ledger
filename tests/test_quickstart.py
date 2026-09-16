from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "chatlog.py"
EXPORT = ROOT / "tests" / "fixtures" / "exports" / "positive" / "representative-export.json"

class QuickstartTest(unittest.TestCase):
    def test_readme_flow_from_clean_checkout(self):
        temp = Path(tempfile.mkdtemp(prefix="ledger-quickstart-"))
        try:
            checkout = temp / "checkout"
            shutil.copytree(ROOT, checkout, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"))
            vault = temp / "private-vault"
            cli = checkout / "scripts" / "chatlog.py"
            commands = [
                [sys.executable, str(cli), "init", "--vault", str(vault)],
                [sys.executable, str(cli), "validate", "--vault", str(vault)],
                [sys.executable, str(cli), "inspect-export", "--input", str(EXPORT)],
                [sys.executable, str(cli), "ingest-export", "--input", str(EXPORT), "--vault", str(vault)],
                [sys.executable, str(cli), "validate", "--vault", str(vault)],
            ]
            for command in commands:
                result = subprocess.run(command, capture_output=True, text=True, check=False)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            report = json.loads(subprocess.run(commands[-1], capture_output=True, text=True, check=True).stdout)
            self.assertTrue(report["ok"])
            self.assertTrue((vault / "00 - ChatGPT Knowledge Ledger.md").is_file())
            self.assertTrue(any((vault / "01 - MOCs" / "Weekly").rglob("*.md")))
        finally:
            shutil.rmtree(temp)

if __name__ == "__main__": unittest.main()
