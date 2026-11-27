"""Local stdio MCP for trusted host-side planners, never sandbox agents."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Literal

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("BI-ntasker")
Priority = Literal["critical", "high", "normal", "low"]


def require(group: str) -> None:
    allowed = os.environ.get("NTASKER_MCP_PERMISSIONS", "read,plan").split(",")
    if group not in {item.strip() for item in allowed}:
        raise PermissionError(f"MCP permission required: {group}")


def cli(*args: str, structured: bool = False) -> dict | list:
    result = subprocess.run(
        [sys.executable, "-m", "ntasker", *args],
        capture_output=True, text=True, timeout=30, check=False,
        stdin=subprocess.DEVNULL,
    )
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout).strip()[:4000])
    if structured:
        return json.loads(result.stdout)
    return {"output": result.stdout.strip()}


def positive(task_id: int) -> str:
    if task_id <= 0:
        raise ValueError("Task id must be positive")
    return str(task_id)


@mcp.tool()
def projects_list() -> dict | list:
    """List projects known to the tracker."""
    require("read")
    return cli("projects", "list", "--json", structured=True)


@mcp.tool()
def tasks_list(project: str | None = None) -> dict | list:
    """List tasks, optionally filtered by project."""
    require("read")
    args = ["list", "--json"]
    if project:
        args.append("--project=" + project)
    return cli(*args, structured=True)


@mcp.tool()
def task_result(task_id: int) -> dict | list:
    """Read task details and stored report."""
    require("read")
    return cli("show", positive(task_id), "--json", structured=True)


@mcp.tool()
def agents_list() -> dict | list:
    """List registered agents."""
    require("read")
    return cli("agent", "list", "--json", structured=True)


@mcp.tool()
def task_create(project: str, title: str, description: str,
                priority: Priority = "normal") -> dict | list:
    """Create a draft for human approval; never starts an agent."""
    require("plan")
    if not project.strip() or not title.strip():
        raise ValueError("Project and title are required")
    return cli("add", "--draft", "--agent=pi", "--model=ollama/ornith-1.5:9b",
               "--project=" + project, "--title=" + title,
               "--description=" + description, "--priority=" + priority)


@mcp.tool()
def task_update(task_id: int, title: str | None = None,
                description: str | None = None, priority: Priority | None = None) -> dict | list:
    """Edit task planning fields without changing status or execution policy."""
    require("plan")
    args = ["patch", positive(task_id)]
    for key, value in (("title", title), ("description", description), ("priority", priority)):
        if value is not None:
            args.append("--" + key + "=" + value)
    if len(args) == 2:
        raise ValueError("No changes supplied")
    return cli(*args)


@mcp.tool()
def task_dependencies(task_id: int, depends_on: list[int]) -> dict | list:
    """Replace dependencies using the tracker's validation."""
    require("plan")
    return cli("patch", positive(task_id), "--depends=" + ",".join(map(positive, depends_on)))


@mcp.tool()
def task_assign(task_id: int, model: Literal["ollama/ornith-1.5:9b"] = "ollama/ornith-1.5:9b") -> dict | list:
    """Assign the approved local Pi model."""
    require("plan")
    return cli("patch", positive(task_id), "--agent=pi", "--model=" + model)


@mcp.tool()
def task_enqueue(task_id: int) -> dict | list:
    """Queue an already approved task; drafts must be released by a human."""
    require("execute")
    return cli("queue", "add", positive(task_id))


@mcp.tool()
def task_review(task_id: int, report: str) -> dict | list:
    """Store a technical review without closing or merging the task."""
    require("review")
    return cli("patch", positive(task_id), "--report=" + report)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
