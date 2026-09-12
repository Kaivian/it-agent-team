import sys
import tempfile
import unittest
from pathlib import Path

pkg_dir = Path(__file__).resolve().parent.parent
if str(pkg_dir.parent) not in sys.path:
    sys.path.insert(0, str(pkg_dir.parent))

from supervisor.file_guard import FileGuard
from supervisor.invariants import InvariantViolationError, validate_disjoint_allowlists, validate_subcoder_sizing
from supervisor.models import AgentRecord, AgentState, ConnectionState, LockType, TaskRecord, TaskStatus
from supervisor.state_store import StateStore


class TestSupervisorModels(unittest.TestCase):
    def test_agent_record_defaults(self):
        agent = AgentRecord(agent_id="sub-coder-01", role="Sub-Coder", model_tier="flash")
        self.assertEqual(agent.state, AgentState.READY)
        self.assertEqual(agent.connection_state, ConnectionState.CONNECTED)
        self.assertEqual(agent.assigned_files, [])
        self.assertIsNotNone(agent.last_heartbeat)

    def test_task_record_defaults(self):
        task = TaskRecord(task_id="TASK-001", name="Init", description="Initialize repository")
        self.assertEqual(task.status, TaskStatus.PENDING)
        self.assertEqual(task.tier, 1)
        self.assertIsNone(task.completed_at)


class TestFileGuard(unittest.TestCase):
    def setUp(self):
        self.guard = FileGuard()

    def test_acquire_and_release_exclusive_lock(self):
        self.assertTrue(self.guard.acquire_lock("src/models.py", "sub-coder-01"))
        self.assertTrue(self.guard.is_locked("src/models.py"))
        self.assertEqual(self.guard.get_lock_holder("src/models.py"), "sub-coder-01")

        # Second agent cannot acquire exclusive lock
        self.assertFalse(self.guard.acquire_lock("src/models.py", "sub-coder-02"))

        # Release lock
        self.assertTrue(self.guard.release_lock("src/models.py", "sub-coder-01"))
        self.assertFalse(self.guard.is_locked("src/models.py"))

        # Now second agent can acquire
        self.assertTrue(self.guard.acquire_lock("src/models.py", "sub-coder-02"))

    def test_case_insensitive_path_normalization(self):
        self.assertTrue(self.guard.acquire_lock("SRC/INDEX.TS", "sub-coder-01"))
        self.assertTrue(self.guard.is_locked("src/index.ts"))
        self.assertFalse(self.guard.acquire_lock("src/index.ts", "sub-coder-02"))

    def test_release_all_for_agent(self):
        self.guard.acquire_lock("file1.ts", "sub-coder-01")
        self.guard.acquire_lock("file2.ts", "sub-coder-01")
        self.guard.acquire_lock("file3.ts", "sub-coder-02")

        released = self.guard.release_all_for_agent("sub-coder-01")
        self.assertEqual(released, 2)
        self.assertFalse(self.guard.is_locked("file1.ts"))
        self.assertFalse(self.guard.is_locked("file2.ts"))
        self.assertTrue(self.guard.is_locked("file3.ts"))


class TestInvariants(unittest.TestCase):
    def test_subcoder_sizing_valid(self):
        # 10 files with 3 coders: 3.33 files/coder <= 5.0 (Pass)
        validate_subcoder_sizing(file_count=10, subcoder_count=3)

    def test_subcoder_sizing_exceeded(self):
        # 12 files with 2 coders: 6.0 files/coder > 5.0 (Violation)
        with self.assertRaises(InvariantViolationError):
            validate_subcoder_sizing(file_count=12, subcoder_count=2)

    def test_disjoint_allowlists_valid(self):
        allocations = {
            "sub-coder-01": ["src/a.py", "src/b.py"],
            "sub-coder-02": ["src/c.py", "src/d.py"],
        }
        validate_disjoint_allowlists(allocations)

    def test_disjoint_allowlists_collision(self):
        allocations = {
            "sub-coder-01": ["src/shared.py", "src/a.py"],
            "sub-coder-02": ["src/shared.py", "src/b.py"],
        }
        with self.assertRaises(InvariantViolationError):
            validate_disjoint_allowlists(allocations)


class TestStateStore(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_file = Path(self.temp_dir.name) / "test_state.db"
        self.store = StateStore(self.db_file)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_register_and_retrieve_agent(self):
        agent = AgentRecord(
            agent_id="pm-agent-01",
            role="Product Manager",
            model_tier="pro",
            state=AgentState.RUNNING,
            assigned_files=["TECHNICAL_SPEC.md"],
        )
        self.store.register_agent(agent)
        retrieved = self.store.get_agent("pm-agent-01")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.agent_id, "pm-agent-01")
        self.assertEqual(retrieved.role, "Product Manager")
        self.assertEqual(retrieved.state, AgentState.RUNNING)
        self.assertEqual(retrieved.assigned_files, ["TECHNICAL_SPEC.md"])

    def test_log_event(self):
        event_id = self.store.log_event(
            timestamp="2026-09-12T11:00:00Z",
            source_agent="Orchestrator",
            target_agent="sub-coder-01",
            action="DISPATCH",
            details="Assigned file1.py",
            status="SUCCESS",
        )
        self.assertGreater(event_id, 0)


if __name__ == "__main__":
    unittest.main()
