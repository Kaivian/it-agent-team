"""Package and installer regression tests; never change the user's home."""
import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import doctor
import install_plugin
import validate_package


class PackagingTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory(prefix="agent-team-package-", dir=ROOT.parent)
        self.directory = Path(self.scratch.name)

    def tearDown(self):
        self.scratch.cleanup()

    def copy_package(self):
        package = self.directory / "package"
        shutil.copytree(ROOT, package, ignore=shutil.ignore_patterns(".git", "__pycache__", ".gemini", ".agent-team", ".agent_team", ".pytest_cache"))
        return package

    def test_current_package(self):
        self.assertFalse([c for c in validate_package.validate(ROOT) if c["status"] == "FAIL"])

    def test_reject_manifest_version_drift(self):
        package = self.copy_package()
        path = package / "gemini-extension.json"
        data = json.loads(path.read_text())
        data["version"] = "0.0.1"
        path.write_text(json.dumps(data))
        checks = validate_package.validate(package)
        self.assertTrue(any(c["check"] == "gemini-extension.json" and c["status"] == "FAIL" for c in checks))

    def test_reject_catalog_escape_and_invalid_policy(self):
        for mutation in ({"source": {"source": "local", "path": "./../"}},
                         {"policy": {"installation": "AUTO", "authentication": "NONE"}}):
            package = self.copy_package()
            path = package / ".agents/plugins/marketplace.json"
            data = json.loads(path.read_text())
            data["plugins"][0].update(mutation)
            path.write_text(json.dumps(data))
            self.assertTrue(any(c["status"] == "FAIL" for c in validate_package.validate(package)))
            shutil.rmtree(package)

    def test_reject_missing_role_and_bad_skill_frontmatter(self):
        package = self.copy_package()
        (package / "agents/sub-coder.md").unlink()
        (package / "skills/agent-team/SKILL.md").write_text("# Missing frontmatter")
        checks = validate_package.validate(package)
        self.assertEqual(2, sum(c["status"] == "FAIL" for c in checks))

    def test_gemini_preserves_unrelated_settings_and_is_idempotent(self):
        path = self.directory / "config.json"
        initial = {"theme": "dark", "plugins": {"other": {"enabled": False},
                   "agent-team": {"custom": 7, "enabled": False}}}
        path.write_text(json.dumps(initial))
        install_plugin.enable_gemini(path)
        data = json.loads(path.read_text())
        self.assertEqual("dark", data["theme"])
        self.assertEqual(initial["plugins"]["other"], data["plugins"]["other"])
        self.assertEqual({"custom": 7, "enabled": True}, data["plugins"]["agent-team"])
        before = path.read_bytes(), path.stat().st_mtime_ns
        install_plugin.enable_gemini(path)
        self.assertEqual(before, (path.read_bytes(), path.stat().st_mtime_ns))

    def test_refuse_malformed_gemini_without_any_deployment(self):
        path = self.directory / "config.json"
        for content in ('{"secret":', '[]', '{"plugins": []}', '{"plugins": {"agent-team": false}}'):
            path.write_text(content)
            with mock.patch.object(install_plugin, "deploy") as deploy, contextlib.redirect_stderr(io.StringIO()):
                result = install_plugin.main(["--host", "gemini", "--config-file", str(path),
                                              "--skills-dir", str(self.directory / "skills")])
            self.assertEqual(1, result)
            self.assertEqual(content, path.read_text())
            deploy.assert_not_called()
            self.assertFalse((self.directory / "skills").exists())

    def test_native_command_exit_status_is_not_ignored(self):
        with mock.patch.object(subprocess, "run", return_value=subprocess.CompletedProcess(["git"], 17)):
            with self.assertRaisesRegex(RuntimeError, "exit 17"):
                install_plugin.run(["git", "pull", "--ff-only"])

    def test_update_refuses_dirty_checkout_and_pull_failure(self):
        target = self.directory / "checkout"
        (target / ".git").mkdir(parents=True)
        with mock.patch.object(shutil, "which", return_value="git"), mock.patch.object(install_plugin, "run", return_value="M file.py"):
            with self.assertRaisesRegex(ValueError, "local changes"):
                install_plugin.deploy(target, ROOT, True, "https://example.test/repo.git")
        with mock.patch.object(shutil, "which", return_value="git"), mock.patch.object(install_plugin, "run", side_effect=["", "https://example.test/repo.git", RuntimeError("exit 1")]):
            with self.assertRaisesRegex(RuntimeError, "exit 1"):
                install_plugin.deploy(target, ROOT, True, "https://example.test/repo.git")

    def test_doctor_core_failure_optional_warning_and_install_query(self):
        package = self.copy_package()
        (package / "scripts/supervisor/supervisor.py").write_text("")
        (package / "scripts/supervisor/dashboard.py").write_text("")
        native = {"installed": [{"name": "agent-team", "marketplaceName": "it-agent-team", "installed": True, "enabled": True}]}
        with mock.patch.object(shutil, "which", return_value="codex"), mock.patch.object(subprocess, "run", return_value=subprocess.CompletedProcess([], 0, json.dumps(native))):
            checks = doctor.diagnose(package, "codex", state_dir=self.directory)
        by_name = {c["check"]: c["status"] for c in checks}
        self.assertEqual("FAIL", by_name["Runtime supervisor"])
        self.assertEqual("WARN", by_name["Optional runtime dashboard"])
        self.assertEqual("PASS", by_name["Codex installation"])
        self.assertEqual("PASS", by_name["State directory"])

    def test_doctor_json_output_is_machine_readable(self):
        config = self.directory / "config.json"
        config.write_text("{}")
        result = subprocess.run([sys.executable, str(ROOT / "scripts/doctor.py"), "--host", "gemini", "--config-file", str(config), "--json"], capture_output=True, text=True)
        data = json.loads(result.stdout)
        self.assertEqual("gemini", data["host"])
        self.assertIn("checks", data)
        self.assertEqual(bool(data["summary"]["fail"]), bool(result.returncode))

    def test_installer_wrapper_uses_only_explicit_test_directories(self):
        config = self.directory / "config.json"
        config.write_text('{"custom": true}')
        skills = self.directory / "skills"
        unrelated = skills / "unrelated"
        unrelated.mkdir(parents=True)
        (unrelated / "SKILL.md").write_text("keep")
        if os.name == "nt":
            shell = shutil.which("pwsh") or shutil.which("powershell")
            command = [shell, "-NoProfile", "-File", str(ROOT / "install.ps1"), "-HostName", "gemini", "-ConfigFile", str(config), "-SkillsDir", str(skills), "-SkipDoctor"]
        else:
            shell = shutil.which("bash")
            command = [shell, str(ROOT / "install.sh"), "--host", "gemini", "--config-file", str(config), "--skills-dir", str(skills), "--skip-doctor"]
        if not shell:
            self.skipTest("Installer shell is unavailable")
        for _ in range(2):
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(json.loads(config.read_text())["custom"])
        self.assertEqual("keep", (unrelated / "SKILL.md").read_text())
        self.assertTrue(all((skills / name / "SKILL.md").exists() for name in validate_package.SKILLS))
        self.assertIn(str((ROOT / "skills/agent-team/SKILL.md").resolve().as_posix()), (skills / "agent-team/SKILL.md").read_text())

    @unittest.skipUnless(os.environ.get("IT_AGENT_TEAM_NATIVE_TESTS") == "1" and shutil.which("codex"), "Opt-in native Codex test")
    def test_native_codex_install_and_reinstall_in_isolated_home(self):
        cache = self.directory / "codex-home"
        cache.mkdir()
        (cache / "config.toml").write_text('model = "test-preserved-model"\n')
        command = [sys.executable, str(ROOT / "scripts/install_plugin.py"), "--codex-home", str(cache), "--skip-doctor"]
        for _ in range(2):
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn('model = "test-preserved-model"', (cache / "config.toml").read_text())
        env = os.environ.copy()
        env["CODEX_HOME"] = str(cache)
        result = subprocess.run(["codex", "plugin", "list", "--json"], env=env, text=True, capture_output=True)
        installed = json.loads(result.stdout)["installed"]
        entry = next(p for p in installed if p["pluginId"] == "agent-team@it-agent-team")
        self.assertTrue(entry["installed"] and entry["enabled"])
        version = json.loads((ROOT / "plugin.json").read_text())["version"]
        installed_root = cache / "plugins/cache/it-agent-team/agent-team" / version
        self.assertTrue(all((installed_root / "skills" / name / "SKILL.md").exists() for name in validate_package.SKILLS))
        self.assertEqual(1, sum(p["pluginId"] == "agent-team@it-agent-team" for p in installed))
        # A different checkout with the same marketplace name must not silently
        # replace an existing user's marketplace source.
        alternate = self.copy_package()
        before = (cache / "config.toml").read_bytes()
        collision = subprocess.run(command + ["--target-dir", str(alternate)], capture_output=True, text=True)
        self.assertNotEqual(0, collision.returncode)
        self.assertEqual(before, (cache / "config.toml").read_bytes())

    @unittest.skipUnless(os.environ.get("IT_AGENT_TEAM_NATIVE_TESTS") == "1" and shutil.which("codex"), "Opt-in native Codex test")
    def test_native_codex_refuses_malformed_toml_without_changes(self):
        cache = self.directory / "bad-codex-home"
        cache.mkdir()
        config = cache / "config.toml"
        original = '[broken\nvalue = "unchanged"\n'
        config.write_text(original)
        result = subprocess.run([sys.executable, str(ROOT / "scripts/install_plugin.py"), "--codex-home", str(cache), "--skip-doctor"], capture_output=True, text=True)
        self.assertNotEqual(0, result.returncode)
        self.assertEqual(original, config.read_text())
        self.assertFalse((cache / "plugins").exists())


if __name__ == "__main__":
    unittest.main()
