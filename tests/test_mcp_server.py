import pytest
from ntasker import mcp_server as server


def test_default_permissions(monkeypatch):
    monkeypatch.delenv("NTASKER_MCP_PERMISSIONS", raising=False)
    with pytest.raises(PermissionError):
        server.task_enqueue(1)


def test_create_draft(monkeypatch):
    monkeypatch.setenv("NTASKER_MCP_PERMISSIONS", "plan")
    monkeypatch.setattr(server, "cli", lambda *args, **kw: args)
    args = server.task_create("Probando", "Test", "--fasttrack")
    assert "--draft" in args
    assert "--description=--fasttrack" in args
    assert "--fasttrack" not in args


def test_dependencies_validate(monkeypatch):
    monkeypatch.setenv("NTASKER_MCP_PERMISSIONS", "plan")
    with pytest.raises(ValueError):
        server.task_dependencies(1, [-2])
