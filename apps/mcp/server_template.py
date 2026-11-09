#!/usr/bin/env python3
"""Template for a new MCP server in apps/mcp/.

How to add a server:
1. Copy this file to apps/mcp/<name>_mcp.py
2. Rename the server and fill in your tools (they read credentials from
   the unified repo-root .env — add a section to env_example.txt).
3. Run it:   python apps/mcp/<name>_mcp.py            # stdio (Vibe VSCode)
              python apps/mcp/<name>_mcp.py --http     # HTTP POST /mcp (Vibe Web)
4. Deploy:   no Docker changes needed — set MCP_ENTRYPOINT=apps/mcp/<name>_mcp.py
              (+ MCP_ARGS="--http --port 8000"), or add a compose service.
"""

from common import create_server, load_env, run_server

load_env()

mcp = create_server("<name>")


@mcp.tool()
async def example_tool() -> dict:
    """Example tool — replace with real ones."""
    return {"ok": True}


if __name__ == "__main__":
    run_server(mcp, "<name> MCP server")
