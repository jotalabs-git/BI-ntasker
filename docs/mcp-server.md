# BI-ntasker MCP (experimental)

Run on the trusted host, not inside an agent sandbox. Default permissions:
read,plan. Tasks created through MCP are drafts; approve them in the UI.
Optional permissions: execute (queue approved tasks), review (store report).
No merge, deletion, automatic approval, or shell execution tool is exposed.
The server delegates to the existing CLI and uses the same local database.

Run make mcp-test and make mcp-integral before connecting Codex.

From the repository root:
```sh
codex mcp add bi-ntasker -- uv --directory "$PWD" run --locked --with 'mcp>=1.12,<2' python -m ntasker.mcp_server
```

The SDK is resolved separately from the application lockfile; pin and audit
its transitive dependencies before production use. The smoke test checks
protocol discovery only. Task stop and diff tools and a full isolated database
integration test are pending. Do not expose this MCP to untrusted agents.
