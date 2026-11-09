#!/usr/bin/env python3
"""
OpenProject MCP Server - Stdio Transport Entry Point

This is the entry point for stdio transport (Vibe for VSCode).
FastMCP-based implementation with automatic tool registration.
"""

from openproject_mcp.server import mcp

if __name__ == "__main__":
    # Run with stdio transport (default for local MCP clients like Vibe VSCode)
    mcp.run(transport="stdio")
