#!/usr/bin/env python3
"""
OpenProject MCP Server - HTTP Transport Entry Point

This is the entry point for HTTP transport (remote agents, e.g. Vibe Web).

Security: HTTP mode REQUIRES a bearer token (MCP_BEARER_TOKEN) and enforces it
on every request. Set MCP_ALLOW_UNAUTHENTICATED=true only for local dev.
"""

import os
import sys

from openproject_mcp.server import mcp
from apps.mcp.common import bearer_auth_middleware, require_bearer_token

if __name__ == "__main__":
    host = os.getenv("MCP_HTTP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_HTTP_PORT", "8000"))

    token = require_bearer_token()

    import uvicorn

    app = mcp.http_app()
    if token:
        app.add_middleware(bearer_auth_middleware(token))

    print(f"Starting OpenProject MCP Server (HTTP)")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Auth: Bearer {'enabled' if token else 'DISABLED (dev mode)'}")

    uvicorn.run(app, host=host, port=port)
