"""Shared boilerplate for all MCP servers in apps/mcp/.

Every server in this directory:
- reads its credentials from the unified repo-root `.env` (via `load_env()`),
- is created with `create_server(name)`,
- is started with the same CLI (`run_server`): stdio by default,
  `--http [--host H] [--port P]` for streamable HTTP (POST /mcp).

Copy `server_template.py` for a new server.
"""

import argparse
from pathlib import Path

from dotenv import load_dotenv
from fastmcp import FastMCP

REPO_ROOT = Path(__file__).resolve().parents[2]


def load_env() -> None:
    """Load the unified .env from the repository root (if present)."""
    load_dotenv(REPO_ROOT / ".env")


def create_server(name: str) -> FastMCP:
    """Create a FastMCP server instance with the given tool prefix."""
    return FastMCP(name)


def run_server(mcp: FastMCP, description: str) -> None:
    """Run the server: stdio by default, streamable HTTP with --http."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--http", action="store_true", help="HTTP transport instead of stdio")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    if args.http:
        mcp.run(transport="http", host=args.host, port=args.port)
    else:
        mcp.run()
