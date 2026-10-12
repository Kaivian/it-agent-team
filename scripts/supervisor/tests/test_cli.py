"""Compact CLI output preserves contracts, failure signals and evidence."""
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from supervisor.__main__ import main, summarize_status
from supervisor.supervisor import Supervisor


class CLIOutputTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manager = Supervisor.initialize(self.root, "CLI output", "cli")
        self.manager.add_tasks([{
            "task_id": "A", "name": "A", "description": "Long requirements " * 100,
            "acceptance_criteria": ["Verified behavior"], "file_allowlist": ["A.txt"],
            "dependencies": [],
        }])

    def run_cli(self, *arguments):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main(["--workspace", str(self.root), "--session", "cli", *arguments])
        return code, output.getvalue()

    def test_summary_is_smaller_and_does_not_change_state_or_full_report(self):
        before = self.manager.status()
        code, full = self.run_cli("status")
        compact_code, compact = self.run_cli("--compact", "status", "--summary")
        self.assertEqual((code, compact_code), (0, 0))
        self.assertEqual(json.loads(full), before)
        summary = json.loads(compact)
        self.assertEqual(summary["counts"], {"READY": 1})
        self.assertEqual(summary["tasks"][0]["task_id"], "A")
        self.assertNotIn("description", summary["tasks"][0])
        self.assertLess(len(compact), len(full) / 2)
        self.assertEqual(len(compact.splitlines()), 1)
        self.assertEqual(self.manager.status(), before)
        _, report = self.run_cli("--compact", "report")
        persisted = json.loads(Path(json.loads(report)["json_report"]).read_text())
        self.assertEqual(persisted["tasks"], before["tasks"])

    def test_compact_claim_retains_full_dispatch_contract_and_token(self):
        code, output = self.run_cli("--compact", "claim", "--worker", "coder")
        claim = json.loads(output)
        self.assertEqual(code, 0)
        self.assertTrue(claim["token"])
        self.assertEqual(claim["task"]["acceptance_criteria"], ["Verified behavior"])
        self.assertEqual(claim["task"]["file_allowlist"], ["a.txt"])

    def test_summary_retains_expiry_dependencies_and_verification_errors(self):
        status = self.manager.status()
        status["tasks"][0].update(status="FAILED", expired=True, dependencies=["B"],
                                  result={"verification_errors": ["Missing evidence"]})
        item = summarize_status(status)["tasks"][0]
        self.assertEqual(item["status"], "FAILED")
        self.assertTrue(item["expired"])
        self.assertEqual(item["dependencies"], ["B"])
        self.assertEqual(item["verification_errors"], ["Missing evidence"])
        status["tasks"] = []
        self.assertEqual(summarize_status(status)["counts"], {})

    def test_compact_failed_check_preserves_receipt_and_exit_status(self):
        receipt = {"check_id": "receipt", "exit_code": 1, "output_path": "failure.txt"}
        with mock.patch.object(Supervisor, "check", return_value=receipt):
            code, output = self.run_cli("--compact", "check", "--task", "A", "--worker", "coder",
                                        "--token", "attempt", "--", "python", "-V")
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(output), receipt)


if __name__ == "__main__":
    unittest.main()
