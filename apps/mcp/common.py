"""Shared boilerplate for all MCP servers in apps/mcp/.

Every server in this directory:
- reads its credentials from the unified repo-root `.env` (via `load_env()`),
- is created with `create_server(name)`,
- is started with the same CLI (`run_server`): stdio by default,
  `--http [--host H] [--port P]` for streamable HTTP (POST /mcp).

Copy `server_template.py` for a new server.
"""

import argparse
import hmac
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastmcp import FastMCP

REPO_ROOT = Path(__file__).resolve().parents[2]


def bearer_auth_middleware(token: str):
    """Starlette middleware enforcing `Authorization: Bearer <token>` (constant-time)."""
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.responses import JSONResponse

    class BearerAuthMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            auth = request.headers.get("authorization", "")
            ok = auth.startswith("Bearer ") and hmac.compare_digest(auth[7:], token)
            if not ok:
                return JSONResponse({"error": "unauthorized"}, status_code=401)
            return await call_next(request)

    return BearerAuthMiddleware


def require_bearer_token() -> str:
    """Return MCP_BEARER_TOKEN or abort: HTTP servers must not run unauthenticated."""
    token = os.environ.get("MCP_BEARER_TOKEN", "")
    if not token and os.environ.get("MCP_ALLOW_UNAUTHENTICATED", "").lower() != "true":
        print("[ERROR] MCP_BEARER_TOKEN is not set — refusing to start an unauthenticated HTTP server.")
        print("        Set MCP_BEARER_TOKEN=<token> (recommended, put it in front via nginx too),")
        print("        or MCP_ALLOW_UNAUTHENTICATED=true for local development only.")
        sys.exit(1)
    if not token:
        print("[WARNING] MCP_ALLOW_UNAUTHENTICATED=true — HTTP server is UNAUTHENTICATED (dev only)!")
    return token


def load_env() -> None:
    """Load the unified .env from the repository root (if present)."""
    load_dotenv(REPO_ROOT / ".env")


def create_server(name: str) -> FastMCP:
    """Create a FastMCP server instance with the given tool prefix."""
    return FastMCP(name)


def run_server(mcp: FastMCP, description: str) -> None:
    """Run the server: stdio by default, streamable HTTP with --http.

    HTTP mode requires MCP_BEARER_TOKEN (enforced via bearer_auth_middleware),
    unless MCP_ALLOW_UNAUTHENTICATED=true is set explicitly (local dev only).
    """
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--http", action="store_true", help="HTTP transport instead of stdio")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    if args.http:
        import uvicorn

        token = require_bearer_token()
        app = mcp.http_app()
        if token:
            app.add_middleware(bearer_auth_middleware(token))
        uvicorn.run(app, host=args.host, port=args.port)
    else:
        mcp.run()
