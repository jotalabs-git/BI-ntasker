"""Execution adapter preflight; no Docker daemon or agent is required."""

import pytest

from ntasker.execution import ExecutionConfigError, plan_launch


def test_local_launch_preserves_agent_command(tmp_path):
    plan = plan_launch(("pi", "--model", "ornith-1.5:9b"), tmp_path)
    assert plan.argv == ("pi", "--model", "ornith-1.5:9b")
    assert plan.cwd == tmp_path.resolve()
    assert plan.backend == "local"


def test_sandbox_plan_uses_explicit_arguments(tmp_path):
    root = tmp_path / "workspaces"
    project = root / "BuenasIdeasERP"
    project.mkdir(parents=True)
    plan = plan_launch(
        ["pi", "--model", "ornith-1.5:9b"],
        project,
        backend="sandbox",
        workspace_root=root,
        sandbox_name="buenasideas-erp-pi",
    )
    assert plan.argv == (
        "sbx", "--no-input", "exec", "-it", "--workdir", str(project.resolve()),
        "buenasideas-erp-pi", "bash", "-ic", 'exec "$@"', "ntasker-agent",
        "pi", "--model", "ornith-1.5:9b"
    )
    assert plan.backend == "sandbox"


@pytest.mark.parametrize("bad_name", ["", "../escape", "two words", "--help", "a/b"])
def test_rejects_unsafe_sandbox_names(tmp_path, bad_name):
    root = tmp_path / "workspaces"
    project = root / "repo"
    project.mkdir(parents=True)
    with pytest.raises(ExecutionConfigError, match="invalid sandbox name"):
        plan_launch(
            ["pi"], project, backend="sandbox", workspace_root=root, sandbox_name=bad_name
        )


def test_rejects_project_outside_root(tmp_path):
    root = tmp_path / "workspaces"
    outside = tmp_path / "original-repository"
    root.mkdir()
    outside.mkdir()
    with pytest.raises(ExecutionConfigError, match="within workspace root"):
        plan_launch(
            ["pi"],
            outside,
            backend="sandbox",
            workspace_root=root,
            sandbox_name="agent-1",
        )


def test_rejects_symlink_escape(tmp_path):
    root = tmp_path / "workspaces"
    outside = tmp_path / "original-repository"
    root.mkdir()
    outside.mkdir()
    (root / "linked").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ExecutionConfigError, match="within workspace root"):
        plan_launch(
            ["pi"],
            root / "linked",
            backend="sandbox",
            workspace_root=root,
            sandbox_name="agent-1",
        )


def test_sandbox_requires_explicit_root_and_name(tmp_path):
    with pytest.raises(ExecutionConfigError, match="workspace root"):
        plan_launch(["pi"], tmp_path, backend="sandbox", sandbox_name="agent")
    root = tmp_path / "workspaces"
    project = root / "repo"
    project.mkdir(parents=True)
    with pytest.raises(ExecutionConfigError, match="invalid sandbox name"):
        plan_launch(["pi"], project, backend="sandbox", workspace_root=root)


def test_invalid_backend_fails_closed(tmp_path):
    with pytest.raises(ExecutionConfigError, match="unsupported"):
        plan_launch(["pi"], tmp_path, backend="unknown")


def test_missing_directory_fails_closed(tmp_path):
    with pytest.raises(FileNotFoundError):
        plan_launch(["pi"], tmp_path / "missing")
