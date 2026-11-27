# SandBoxLab execution architecture (work in progress)

This fork preserves ntasker's local task runner and adds an **opt-in**
execution adapter for Docker Sandbox (SBX). The first step is a pure
launch-planning module, `ntasker.execution`, with unit tests. **Sandbox
execution is not enabled by this commit.**

## Local laboratory

- Lab root: `/mnt/d8t/AGENTES/SandBoxLab`
- Project copies: `/mnt/d8t/AGENTES/SandBoxLab/workspaces/<project>`
- Sample sandbox: `buenasideas-erp-pi`
- Template: `sandboxlab/pi:node24`
- Agent: Pi 1.6.1, Ollama `ornith-1.5:9b` on the Linux host
- Important: the host's real repositories must never be mounted inside an
  agent sandbox, directly or through a symlink.

## Design boundaries

1. **Control plane**: ntasker runs as a local-only web service and owns its
   SQLite database, queue, comments and review workflow.
2. **Execution plane**: a selected SBX instance owns the agent process and
   can access only its designated project copy.
3. **Provisioning**: creating/cloning workspaces and setting up sandboxes
   will be separate from starting an individual task.
4. **Integration**: no automatic Git push, merge or commit to the original
   repository. Review and Git integration require an explicit human action.
5. **Network**: a local model alone does not prevent outbound traffic;
   separately enforce SBX network policies.
6. **Trust**: a path validator is a defense-in-depth check, **not** an
   isolation boundary. Actual mounts, Docker/SBX permissions and link
   traversal must be verified by integration tests.
7. **Security**: ntasker is unauthenticated by default; keep it bound to
   `127.0.0.1` and do not expose its HTTP API on a LAN or the Internet.

## Staged implementation

### Phase 1 — pure launch planning (this commit)

- Introduce `LaunchPlan` and `plan_launch()`.
- Keep local execution as the default.
- Validate existing directories, workspace boundaries and sandbox names.
- Add tests for symlink escape, invalid names, invalid backends and the
  original local command.

### Phase 2 — SBX integration

Verify the actual SBX CLI from a Linux host (`sbx run --help`,
`sbx list`) before connecting the adapter to the existing PTY runner.
Check whether the CLI supports an arbitrary command in a named sandbox
and whether it forwards raw TTY input, terminal resize, interrupts and
process exit signals. Never assume a local `subprocess.Popen` of
`sbx run` is sufficient. No fallback to host Pi if SBX is unavailable.

### Phase 3 — isolation, task lifecycle and UI

- Sandbox registry and per-project assignment.
- Preflight checks before queue dispatch.
- Explicit stop/restart controls and robust session cleanup.
- File path/mount checks and repository-original isolation tests.
- Review-first Git integration and audit events.
- Local Ollama monitoring and conservative concurrency limits.
- Spanish UI and optional Claude-free task triage.

## Running tests

```bash
uv run pytest tests/test_execution.py
```

Nothing in Phase 1 changes runtime dispatch or installs any software on the
host. Do **not** configure an `sbx` binary override in the UI yet.
