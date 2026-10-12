"""Integration tests for evidence gates, process coordination and recovery."""
import json
import multiprocessing
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SCRIPTS))
from supervisor.file_guard import FileGuard
from supervisor.models import LockType
from supervisor.supervisor import Supervisor
from supervisor.recovery_manager import recover
from supervisor.reporting import generate_report
from supervisor.task_queue import TaskQueue
from supervisor.task_validator import validate_tasks


def task(tid="A", paths=None, deps=None):
    return {"task_id": tid, "name": "Edit " + tid, "description": "Implement a toy change",
            "acceptance_criteria": ["The file contains the expected text and its check passes"],
            "file_allowlist": paths if paths is not None else [tid + ".txt"], "dependencies": deps or []}


def lock_contender(root, owner, start, release, results):
    try:
        guard = FileGuard(workspace=root)
        start.wait(20)
        acquired = guard.acquire_lock("shared.txt", owner)
        results.put((owner, acquired))
        if acquired:
            release.wait(20)
            guard.release_lock("shared.txt", owner)
    except Exception as exc:
        results.put((owner, str(exc)))


def claim_contender(root, sid, owner, results):
    try:
        claim = Supervisor(root, sid).claim(owner)
        results.put(claim["task"]["task_id"] if claim else None)
    except Exception as exc:
        results.put("ERROR: " + str(exc))


class SessionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.manager = Supervisor.initialize(self.root, "Toy implementation", "session", concurrency=2)

    def tearDown(self):
        self.temp.cleanup()

    def check(self, claim, code="pass"):
        return self.manager.check(claim["task"]["task_id"], claim["worker"], claim["token"], [sys.executable, "-c", code])

    def submit(self, claim, checks=(), files=None, status="completed"):
        return self.manager.submit(claim["task"]["task_id"], claim["worker"], claim["token"],
                                   {"status": status, "changed_files": files or [], "check_ids": list(checks), "summary": "Toy task result"})

    def test_dag_dependency_gating_and_restart(self):
        self.manager.add_tasks([task("B", deps=["A"]), task("A")])
        first = self.manager.claim("worker1")
        self.assertEqual(first["task"]["task_id"], "A")
        self.assertIsNone(self.manager.claim("worker2"))
        (self.root / "A.txt").write_text("done", encoding="utf-8")
        receipt = self.check(first, "from pathlib import Path; assert Path('A.txt').read_text() == 'done'")
        self.assertEqual(self.submit(first, [receipt["check_id"]], ["A.txt"])["status"], "COMPLETED")
        restarted = Supervisor(self.root, "session")
        self.assertEqual(restarted.claim("worker2")["task"]["task_id"], "B")

    def test_cycles_missing_dependencies_and_confinement_rejected(self):
        invalid = ([task("A", deps=["B"]), task("B", deps=["A"])], [task("A", deps=["absent"])],
                   [task(paths=["../outside.txt"])], [task(paths=[".agent-team/state.db"])], [task(paths=["src/*.py"])])
        for contracts in invalid:
            with self.subTest(contracts=contracts), self.assertRaises(ValueError):
                self.manager.add_tasks(contracts)
        self.assertEqual(self.manager.status()["tasks"], [])

    def test_no_evidence_and_fabricated_receipt_cannot_complete(self):
        self.manager.add_tasks([task()])
        first = self.manager.claim("worker")
        result = self.submit(first, ["invented"])
        self.assertEqual(result["status"], "FAILED")
        self.assertTrue(any("Unknown check" in reason for reason in result["verification_errors"]))
        with self.assertRaises(ValueError):
            self.submit(first)

    def test_failing_check_cannot_be_hidden_by_omitting_receipt(self):
        self.manager.add_tasks([task()])
        first = self.manager.claim("worker")
        bad = self.check(first, "raise SystemExit(3)")
        good = self.check(first)
        self.assertEqual(bad["exit_code"], 3)
        self.assertEqual(self.submit(first, [good["check_id"]])["status"], "FAILED")

    def test_failed_check_can_be_rerun_successfully(self):
        self.manager.add_tasks([task()])
        first = self.manager.claim("worker")
        command = [sys.executable, "-c", "from pathlib import Path; assert Path('A.txt').exists()"]
        bad = self.manager.check("A", "worker", first["token"], command)
        self.assertNotEqual(bad["exit_code"], 0)
        (self.root / "A.txt").write_text("fixed", encoding="utf-8")
        good = self.manager.check("A", "worker", first["token"], command)
        self.assertEqual(self.submit(first, [good["check_id"]], ["A.txt"])["status"], "COMPLETED")

    def test_actual_unreported_outside_allowlist_edit_fails(self):
        self.manager.add_tasks([task()])
        first = self.manager.claim("worker")
        (self.root / "unauthorized.txt").write_text("edit", encoding="utf-8")
        receipt = self.check(first)
        result = self.submit(first, [receipt["check_id"]])
        self.assertEqual(result["status"], "FAILED")
        self.assertIn("unauthorized.txt", " ".join(result["verification_errors"]))

    def test_unreported_allowed_edit_and_post_check_edit_fail(self):
        self.manager.add_tasks([task()])
        first = self.manager.claim("worker")
        receipt = self.check(first)
        (self.root / "A.txt").write_text("edited after verification", encoding="utf-8")
        result = self.submit(first, [receipt["check_id"]])
        self.assertEqual(result["status"], "FAILED")
        self.assertTrue(any("current contents" in reason for reason in result["verification_errors"]))
        self.assertTrue(any("does not match" in reason for reason in result["verification_errors"]))

    def test_verification_command_mutation_fails_gate(self):
        self.manager.add_tasks([task()])
        first = self.manager.claim("worker")
        receipt = self.check(first, "from pathlib import Path; Path('A.txt').write_text('mutation')")
        self.assertEqual(receipt["exit_code"], 0)
        self.assertEqual(self.submit(first, [receipt["check_id"]], ["A.txt"])["status"], "FAILED")

    def test_parallel_disjoint_workers_complete_despite_peer_changes(self):
        self.manager.add_tasks([task("A"), task("B")])
        first, second = self.manager.claim("worker1"), self.manager.claim("worker2")
        (self.root / "A.txt").write_text("first", encoding="utf-8")
        receipt1 = self.check(first)
        (self.root / "B.txt").write_text("second", encoding="utf-8")
        receipt2 = self.check(second)
        self.assertEqual(self.submit(first, [receipt1["check_id"]], ["A.txt"])["status"], "COMPLETED")
        self.assertEqual(self.submit(second, [receipt2["check_id"]], ["B.txt"])["status"], "COMPLETED")
        self.assertEqual(self.manager.status()["status"], "COMPLETED")

    def test_read_only_final_check_catches_changed_dependency_after_check(self):
        self.manager.add_tasks([task("A"), task("integration", paths=[], deps=["A"])])
        first = self.manager.claim("worker")
        (self.root / "A.txt").write_text("first", encoding="utf-8")
        receipt = self.check(first)
        self.assertEqual(self.submit(first, [receipt["check_id"]], ["A.txt"])["status"], "COMPLETED")
        integration = self.manager.claim("integration-worker")
        checked = self.check(integration, "from pathlib import Path; assert Path('A.txt').read_text() == 'first'")
        (self.root / "A.txt").write_text("changed after verification", encoding="utf-8")
        result = self.submit(integration, [checked["check_id"]])
        self.assertEqual(result["status"], "FAILED")
        self.assertTrue(any("current contents" in reason for reason in result["verification_errors"]))

    def test_unscoped_read_only_check_uses_full_workspace_fingerprint(self):
        (self.root / "source.txt").write_text("original", encoding="utf-8")
        self.manager.add_tasks([task(paths=[])])
        first = self.manager.claim("worker")
        receipt = self.check(first)
        self.assertTrue(receipt["full_workspace_scope"])
        (self.root / "source.txt").write_text("changed", encoding="utf-8")
        self.assertEqual(self.submit(first, [receipt["check_id"]])["status"], "FAILED")

    def test_declared_read_input_shared_lock_blocks_other_session_writer(self):
        (self.root / "input.txt").write_text("stable", encoding="utf-8")
        contract = task()
        contract["verification_files"] = ["input.txt"]
        self.manager.add_tasks([contract])
        self.manager.claim("worker")
        writer = Supervisor.initialize(self.root, "Write input", "writer")
        writer.add_tasks([task("input-edit", paths=["input.txt"])])
        self.assertIsNone(writer.claim("writer"))
        recover(self.manager, "A", True)
        self.assertIsNotNone(writer.claim("writer"))

    def test_same_session_task_ids_in_different_state_roots_do_not_share_lock_owner(self):
        self.manager.add_tasks([task()])
        self.manager.claim("worker")
        alternative = Supervisor.initialize(self.root, "Different state root", "session", state_dir=".gemini/agent-team")
        alternative.add_tasks([task()])
        self.assertIsNone(alternative.claim("worker2"))
        self.assertNotEqual(self.manager.owner("A"), alternative.owner("A"))
        recover(self.manager, "A", True)
        self.assertIsNotNone(alternative.claim("worker2"))

    def test_excluded_dependency_and_cache_paths_cannot_bypass_freshness(self):
        for path in ("node_modules/vendor/index.js", ".pytest_cache/state", "src/__pycache__/cached.pyc", ".agent-team/state.db", ".git"):
            for field in ("file_allowlist", "verification_files"):
                contract = task()
                contract[field] = [path]
                with self.subTest(path=path, field=field), self.assertRaises(ValueError):
                    self.manager.add_tasks([contract])

    @unittest.skipUnless(os.name == "nt", "Windows-only aliases")
    def test_windows_file_aliases_and_streams_rejected(self):
        for path in ("A.txt:stream", "A.txt.", "NUL", "folder/COM1.txt", "A.txt "):
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.manager.add_tasks([task(paths=[path])])

    def test_previously_successful_omitted_check_must_be_fresh(self):
        self.manager.add_tasks([task()])
        first = self.manager.claim("worker")
        self.check(first, "assert True")
        (self.root / "A.txt").write_text("later change", encoding="utf-8")
        latest = self.check(first)
        self.assertEqual(self.submit(first, [latest["check_id"]], ["A.txt"])["status"], "FAILED")

    def test_symlink_state_root_outside_workspace_refused(self):
        with tempfile.TemporaryDirectory() as outside:
            link = self.root / "outside-state"
            try:
                link.symlink_to(outside, target_is_directory=True)
            except OSError:
                self.skipTest("Directory symlink creation is unavailable on this host")
            with self.assertRaises(ValueError):
                Supervisor.initialize(self.root, "Forbidden state", "outside", state_dir="outside-state")
            self.assertFalse((Path(outside) / "sessions").exists())

    def test_worker_identity_and_attempt_token_protect_transitions(self):
        self.manager.add_tasks([task()])
        first = self.manager.claim("worker")
        with self.assertRaises(ValueError):
            self.manager.heartbeat("A", "other", first["token"])
        with self.assertRaises(ValueError):
            self.manager.check("A", "worker", "stale-token", [sys.executable, "-c", "pass"])
        with self.manager.connect(write=True) as conn:
            row = conn.execute("SELECT * FROM tasks WHERE task_id='A'").fetchone()
            with self.assertRaises(ValueError):
                self.manager.transition(conn, row, "COMPLETED")

    def test_cross_session_conflict_retained_until_explicit_recovery(self):
        self.manager.add_tasks([task()])
        self.manager.claim("worker")
        other = Supervisor.initialize(self.root, "Other session", "second")
        other.add_tasks([task()])
        self.assertIsNone(other.claim("worker2"))
        with self.assertRaises(ValueError):
            recover(self.manager, "A", retry=True)
        recover(self.manager, "A", confirm_worker_stopped=True)
        self.assertIsNotNone(other.claim("worker2"))

    def test_recovery_retains_attempt_history_and_has_bounded_retry(self):
        self.manager.add_tasks([task()])
        first = self.manager.claim("worker")
        recover(self.manager, "A", True, retry=True)
        second = Supervisor(self.root, "session").claim("worker")
        self.assertEqual(second["attempt"], 2)
        self.assertNotEqual(first["token"], second["token"])
        with self.assertRaises(ValueError):
            self.manager.heartbeat("A", "worker", first["token"])
        with self.assertRaises(ValueError):
            recover(self.manager, "A", True, retry=True)
        report = generate_report(self.manager)
        events = (self.manager.directory / "events.jsonl").read_text(encoding="utf-8")
        self.assertIn("RECOVERED", events)
        self.assertIn(first["token"], events)
        self.assertTrue(Path(report["markdown_report"]).is_file())

    def test_expired_lease_requires_recovery_not_automatic_replay(self):
        self.manager.add_tasks([task()])
        first = self.manager.claim("worker")
        with self.manager.connect(write=True) as conn:
            conn.execute("UPDATE tasks SET heartbeat=0 WHERE task_id='A'")
        with self.assertRaises(ValueError):
            self.manager.heartbeat("A", "worker", first["token"])
        self.assertTrue(self.manager.status()["tasks"][0]["expired"])
        self.assertTrue(self.manager.guard.is_locked("A.txt"))

    def test_check_timeout_blocks_and_retains_lock(self):
        manager = Supervisor.initialize(self.root, "Timeout", "timeout", timeout=1)
        manager.add_tasks([task()])
        claim = manager.claim("worker")
        receipt = manager.check("A", "worker", claim["token"], [sys.executable, "-c", "import time; time.sleep(3)"])
        self.assertTrue(receipt["timed_out"])
        self.assertEqual(manager.status()["tasks"][0]["status"], "BLOCKED")
        self.assertTrue(manager.guard.is_locked("A.txt"))
        recover(manager, "A", True)
        self.assertFalse(manager.guard.is_locked("A.txt"))

    def test_legacy_state_directory_is_preserved_and_excluded(self):
        manager = Supervisor.initialize(self.root, "Legacy placement", "legacy", state_dir=".gemini")
        manager.add_tasks([task()])
        first = manager.claim("worker")
        (self.root / ".gemini" / "legacy-history.txt").write_text("keep this", encoding="utf-8")
        receipt = manager.check("A", "worker", first["token"], [sys.executable, "-c", "pass"])
        result = manager.submit("A", "worker", first["token"], {"status": "completed", "changed_files": [], "check_ids": [receipt["check_id"]], "summary": "Read-only result"})
        self.assertEqual(result["status"], "COMPLETED")
        self.assertTrue((self.root / ".gemini" / "legacy-history.txt").exists())
        with self.assertRaises(ValueError):
            validate_tasks([task("B", paths=[".gemini/foo"])], self.root, state_dir=".gemini")

    def test_invalid_configuration_and_duplicate_session_refused(self):
        for config in ({"concurrency": 0}, {"timeout": -1}, {"max_retries": 11}, {"workflow": "unknown"}):
            with self.subTest(config=config), self.assertRaises(ValueError):
                Supervisor.initialize(self.root, "invalid", "invalid", **config)
        with self.assertRaises(FileExistsError):
            Supervisor.initialize(self.root, "cannot replace", "session")


class ProcessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.context = multiprocessing.get_context("spawn")

    def tearDown(self):
        self.temp.cleanup()

    def test_exclusive_lock_contended_by_separate_processes(self):
        start, release, results = self.context.Event(), self.context.Event(), self.context.Queue()
        processes = [self.context.Process(target=lock_contender, args=(str(self.root), f"worker{i}", start, release, results)) for i in range(4)]
        try:
            for process in processes:
                process.start()
            start.set()
            outcomes = [results.get(timeout=20) for _ in processes]
            self.assertEqual(sum(value is True for _, value in outcomes), 1, outcomes)
            self.assertTrue(all(type(value) is bool for _, value in outcomes), outcomes)
        finally:
            release.set()
            for process in processes:
                process.join(20)
                if process.is_alive():
                    process.terminate()
                    process.join()
            results.close()

    def test_shared_multi_holder_upgrade_release_and_confinement(self):
        one, two = FileGuard(workspace=self.root), FileGuard(workspace=self.root)
        self.assertTrue(one.acquire_lock("file.txt", "one", LockType.SHARED))
        self.assertTrue(two.acquire_lock("file.txt", "two", LockType.SHARED))
        self.assertEqual(one.get_lock_holders("file.txt"), ["one", "two"])
        self.assertFalse(one.acquire_lock("file.txt", "one", LockType.EXCLUSIVE))
        self.assertTrue(two.release_lock("file.txt", "two"))
        self.assertTrue(one.acquire_lock("file.txt", "one", LockType.EXCLUSIVE))
        self.assertTrue(one.acquire_lock("file.txt", "one", LockType.SHARED))
        self.assertFalse(two.acquire_lock("file.txt", "two", LockType.SHARED))
        with self.assertRaises(ValueError):
            one.acquire_lock("../outside.txt", "one")

    def test_atomic_claim_respects_concurrency_across_processes(self):
        manager = Supervisor.initialize(self.root, "Concurrent claims", "claims", concurrency=2)
        manager.add_tasks([task("A"), task("B"), task("C"), task("D")])
        results = self.context.Queue()
        processes = [self.context.Process(target=claim_contender, args=(str(self.root), "claims", f"worker{i}", results)) for i in range(4)]
        try:
            for process in processes:
                process.start()
            outcomes = [results.get(timeout=20) for _ in processes]
            claimed = [value for value in outcomes if value is not None]
            self.assertEqual(len(claimed), 2, outcomes)
            self.assertEqual(len(set(claimed)), 2)
            self.assertFalse(any(str(value).startswith("ERROR:") for value in claimed), outcomes)
        finally:
            for process in processes:
                process.join(20)
                if process.is_alive():
                    process.terminate()
                    process.join()
            results.close()

    def cli(self, *args, expected=0):
        env = {**os.environ, "PYTHONPATH": str(SCRIPTS)}
        process = subprocess.run([sys.executable, "-m", "supervisor", "--workspace", str(self.root), "--session", "cli", *args],
                                 env=env, capture_output=True, text=True, timeout=20)
        self.assertEqual(process.returncode, expected, process.stdout + process.stderr)
        return json.loads(process.stdout if expected != 2 else process.stderr)

    def test_cli_real_edit_verify_submit_and_restart_report(self):
        self.cli("init", "--objective", "CLI test")
        state = self.root / ".agent-team" / "sessions" / "cli"
        contracts = state / "tasks.json"
        contracts.write_text(json.dumps([task()]), encoding="utf-8")
        self.cli("add", "--tasks", str(contracts))
        claim = self.cli("claim", "--worker", "worker")
        subprocess.run([sys.executable, "-c", "from pathlib import Path; Path('A.txt').write_text('verified')"], cwd=self.root, check=True, timeout=10)
        receipt = self.cli("check", "--task", "A", "--worker", "worker", "--token", claim["token"], "--", sys.executable, "-c",
                           "from pathlib import Path; assert Path('A.txt').read_text() == 'verified'")
        result = state / "result.json"
        result.write_text(json.dumps({"status": "completed", "changed_files": ["A.txt"], "check_ids": [receipt["check_id"]], "summary": "Verified toy edit"}), encoding="utf-8")
        self.assertEqual(self.cli("submit", "--task", "A", "--worker", "worker", "--token", claim["token"], "--result", str(result))["status"], "COMPLETED")
        self.assertEqual(self.cli("status")["status"], "COMPLETED")
        self.assertTrue(Path(self.cli("report")["json_report"]).is_file())

    def test_process_crash_and_explicit_resume_do_not_replay(self):
        manager = Supervisor.initialize(self.root, "Crash test", "crash")
        manager.add_tasks([task()])
        env = {**os.environ, "PYTHONPATH": str(SCRIPTS)}
        script = "from supervisor.supervisor import Supervisor; import json,os,sys; c=Supervisor(sys.argv[1],'crash').claim('worker'); print(json.dumps(c),flush=True); os._exit(7)"
        dead = subprocess.run([sys.executable, "-c", script, str(self.root)], env=env, capture_output=True, text=True, timeout=10)
        self.assertEqual(dead.returncode, 7)
        claim = json.loads(dead.stdout)
        restarted = Supervisor(self.root, "crash")
        self.assertEqual(restarted.status()["tasks"][0]["status"], "RUNNING")
        self.assertIsNone(restarted.claim("new-worker"))
        recovered = recover(restarted, "A", True, retry=True)
        self.assertFalse(recovered["automatic_replay"])
        self.assertFalse((self.root / "A.txt").exists())
        new = restarted.claim("new-worker")
        self.assertNotEqual(new["token"], claim["token"])
        self.assertEqual(new["attempt"], 2)


class QueueIntegrityTests(unittest.TestCase):
    def test_corruption_refused_and_failed_batch_not_completed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "queue.json"
            path.write_text("{invalid", encoding="utf-8")
            with self.assertRaises(ValueError):
                TaskQueue(path)
            path.unlink()
            queue = TaskQueue(path)
            queue.initialize_batch("batch", [("one", "desc"), ("two", "desc")])
            queue.start_current_task("one")
            queue.complete_current_task(False)
            queue.start_current_task("two")
            queue.complete_current_task(True)
            self.assertEqual(TaskQueue(path).batch.status, "FAILED")


if __name__ == "__main__":
    unittest.main()
