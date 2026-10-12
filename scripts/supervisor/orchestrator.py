"""Codex-compatible host-mediated dispatch with an explicit serial fallback."""


class HostAdapter:
    """The caller supplies the actual host callback; no fictitious tools.

    Callback receives the claim envelope and returns its real host handle.
    Without a callback the envelope is returned for execution by the caller.
    """
    def __init__(self, spawn_worker=None):
        self.spawn_worker = spawn_worker

    def dispatch(self, envelope):
        if envelope is None:
            return None
        return {"envelope": envelope, "mode": "delegated" if self.spawn_worker else "serial",
                "host_handle": self.spawn_worker(envelope) if self.spawn_worker else None}


class Orchestrator:
    def __init__(self, manager, adapter=None):
        self.manager = manager
        self.adapter = adapter or HostAdapter()

    def dispatch(self, worker):
        return self.adapter.dispatch(self.manager.claim(worker))
