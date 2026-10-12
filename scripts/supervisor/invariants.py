"""Invariant verification engine for IT Agent Team platform architecture."""

import os
from pathlib import Path


class InvariantViolationError(Exception):
    def __init__(self, invariant_code: str, message: str):
        super().__init__(f"[{invariant_code}] {message}")
        self.invariant_code = invariant_code


def validate_subcoder_sizing(file_count: int, subcoder_count: int, max_files_per_coder: int = 5) -> None:
    if max_files_per_coder <= 0:
        raise ValueError("max_files_per_coder must be positive")
    if file_count <= 0:
        return
    if subcoder_count <= 0:
        raise InvariantViolationError(
            "INVARIANT-012",
            "At least one sub-coder must be allocated for non-empty tasks.",
        )
    files_per_coder = file_count / subcoder_count
    if files_per_coder > max_files_per_coder:
        raise InvariantViolationError(
            "INVARIANT-003",
            f"Sub-coder file ceiling exceeded: {files_per_coder:.1f} files/agent (maximum allowed: {max_files_per_coder}).",
        )


def validate_disjoint_allowlists(allocations: dict[str, list[str]]) -> None:
    seen_files: dict[str, str] = {}
    for agent_id, files in allocations.items():
        for f in files:
            norm = os.path.normcase(str(Path(f).resolve()))
            if norm in seen_files:
                raise InvariantViolationError(
                    "INVARIANT-004",
                    f"Disjoint allowlist collision on file '{f}' between '{seen_files[norm]}' and '{agent_id}'.",
                )
            seen_files[norm] = agent_id
