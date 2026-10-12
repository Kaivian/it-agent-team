"""Protect project instructions when exporting optional workflow guidance."""

import importlib.util
from pathlib import Path
import tempfile
import unittest


spec = importlib.util.spec_from_file_location("export_rules", Path(__file__).resolve().parents[1] / "scripts/export_rules.py")
exporter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exporter)


class ExportRulesTests(unittest.TestCase):
    def test_existing_instructions_abort_before_other_writes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.md"
            source.write_text("Team guidance", encoding="utf-8")
            project = root / "project"
            project.mkdir()
            (project / "AGENTS.md").write_text("Project guidance", encoding="utf-8")
            self.assertEqual(exporter.export_rules(source, project, ["all"]), 1)
            self.assertEqual((project / "AGENTS.md").read_text(), "Project guidance")
            self.assertFalse((project / ".github").exists())

    def test_explicit_replacement_and_fresh_export(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.md"
            source.write_text("Team guidance", encoding="utf-8")
            project = root / "project"
            self.assertEqual(exporter.export_rules(source, project, ["universal"]), 0)
            source.write_text("Updated guidance", encoding="utf-8")
            self.assertEqual(exporter.export_rules(source, project, ["universal"], replace=True), 0)
            self.assertEqual((project / "AGENTS.md").read_text(), "Updated guidance")


if __name__ == "__main__":
    unittest.main()
