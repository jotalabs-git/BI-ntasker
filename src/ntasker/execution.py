"""Execution adapters for interactive agent processes.

This module only plans commands. It does not create or start sandboxes.
The default local adapter leaves existing ntasker behaviour unchanged.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Sequence

ExecutionBackend = Literal["local", "sandbox"]

_SANDBOX_NAME = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]$")


class ExecutionConfigError(ValueError):
    """An execution request cannot satisfy the configured isolation policy."""


@dataclass(frozen=True)
class LaunchPlan:
    argv: tuple[str, ...]
    cwd: Path
    backend: ExecutionBackend


def plan_launch(
    argv: Sequence[str],
    cwd: str | os.PathLike[str],
    *,
    backend: ExecutionBackend = "local",
    workspace_root: str | os.PathLike[str] | None = None,
    sandbox_name: str | None = None,
    sbx_binary: str = "sbx",
) -> LaunchPlan:
    """Prepare an agent launch without executing arbitrary shell text.

    A sandbox plan must refer to an existing workspace nested under the
    configured root. Paths are resolved to reject symlinks escaping that root.
    Provisioning and PTY attachment are deliberately separate concerns.
    """
    if not argv or not argv[0]:
        raise ExecutionConfigError("agent command must not be empty")
    workdir = Path(cwd).expanduser().resolve(strict=True)
    if not workdir.is_dir():
        raise ExecutionConfigError("agent working directory is not a directory")
    if backend == "local":
        return LaunchPlan(tuple(argv), workdir, "local")
    if backend != "sandbox":
        raise ExecutionConfigError(f"unsupported execution backend: {backend}")
    if not workspace_root:
        raise ExecutionConfigError("sandbox backend requires a workspace root")
    root = Path(workspace_root).expanduser().resolve(strict=True)
    if not root.is_dir() or workdir == root or not workdir.is_relative_to(root):
        raise ExecutionConfigError("sandbox working directory must be within workspace root")
    if not sandbox_name or not _SANDBOX_NAME.fullmatch(sandbox_name):
        raise ExecutionConfigError("invalid sandbox name")
    if not sbx_binary or "/" in sbx_binary or not re.fullmatch(r"[a-zA-Z0-9_-]+", sbx_binary):
        raise ExecutionConfigError("invalid sbx binary name")
    # Attach only to an existing, explicitly approved sandbox.
    return LaunchPlan(
        (sbx_binary, "--no-input", "exec", "-it", "--workdir", str(workdir), sandbox_name, *argv),
        workdir,
        "sandbox",
    )
