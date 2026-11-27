"""Exercise MCP initialization and tool discovery without changing the database."""
import asyncio
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    params = StdioServerParameters(command=sys.executable, args=["-m", "ntasker.mcp_server"])
    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = {tool.name for tool in tools.tools}
            assert {"task_create", "tasks_list", "task_enqueue", "task_review"} <= names
            print("MCP stdio discovery OK:", sorted(names))


if __name__ == "__main__":
    asyncio.run(main())
