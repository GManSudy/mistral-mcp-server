# OpenProject MCP — Mistral & Claude Edition

An **optimized fork of the OpenProject MCP server** (Python / FastMCP, OpenProject API v3),
specialized for **Mistral** (Studio / Vibe Web & Vibe for VSCode) and **Claude**
(Claude Code / Claude Desktop) agents.

Original project: 👉 https://github.com/AndyEverything/openproject-mcp-server — see
[Credits](#-credits).

> 🇩🇪 Detailed German guide: [`AGENT.md`](AGENT.md). Claude-specific docs:
> [`CLAUDE_CODE_SETUP.md`](CLAUDE_CODE_SETUP.md) and [`CLAUDE_CODE_GUIDE.md`](CLAUDE_CODE_GUIDE.md).

## ✨ What's optimized in this fork

- 🐳 **Fixed `Dockerfile`** — upstream `CMD` pointed to a non-existent `openproject-mcp.py`;
  now starts `openproject-mcp-fastmcp.py` and exposes port 8000
- 📦 **Complete `requirements.txt`** — upstream missed `fastmcp`, `pydantic`, `uvicorn`,
  `starlette` (only installable via `pyproject.toml`)
- 🧹 **Removed the 138 KB legacy monolith** (`openproject-mcp.legacy.py`) — dead code
- 🏷️ **Packaging metadata** — real author, repo URLs (`Repository` / `Upstream`), version bump
- 📖 **Step-by-step agent setup** (below) for Mistral Vibe and Claude Code

---

## 📋 Prerequisites

- An **OpenProject instance** (cloud or self-hosted) and an **API key**
- **Python 3.10+** and [uv](https://docs.astral.sh/uv/) (or plain pip)
- A **Mistral account** (Studio / Vibe) *or* **Claude Code / Claude Desktop** installed
- For Mistral Vibe **Web** (cloud): a server with a **public HTTPS URL** (e.g. a VM with
  nginx + Let's Encrypt) — see Step 4

---

## 🚀 Step-by-Step Setup

### Step 1 — Clone and set up this repository

```bash
git clone https://github.com/GManSudy/openproject-mcp.git
cd openproject-mcp-server
uv sync          # or: pip install -r requirements.txt
```

### Step 2 — Configure the server

```bash
cp env_example.txt .env
```

Edit `.env`:

```env
OPENPROJECT_URL=https://your-instance.openproject.com
OPENPROJECT_API_KEY=your-api-key-here
```

**Get the API key in OpenProject:** Avatar → *My account* → *Access tokens* → *+ Add*.
The server authenticates with `Authorization: Basic base64("apikey:" + KEY)` —
`Authorization: ApiKey <token>` is **rejected** by OpenProject.

### Step 3 — Start the server (pick one transport)

**stdio** (local agents: Vibe for VSCode, Claude Code/Desktop):

```bash
uv run openproject-mcp-fastmcp.py
```

**streamable HTTP** (Mistral Studio / Vibe Web, remote agents):

```bash
uv run openproject-mcp-http.py     # default 0.0.0.0:8000, endpoint POST /mcp
```

**Docker:**

```bash
docker build -t openproject-mcp .
docker run --env-file .env -p 8000:8000 openproject-mcp
```

Local smoke test (HTTP mode): set `MCP_HTTP_HOST=127.0.0.1`, then send an MCP
`initialize` request to `http://127.0.0.1:8000/mcp` → expect HTTP 200 with a session ID.

### Step 4 — Connect Mistral Vibe Web (Studio) via Custom MCP Connector

Studio/Vibe Web run in the cloud, so the MCP endpoint needs a **publicly reachable
HTTPS URL with auth in front**:

1. Run the HTTP server on a VM (e.g. OpenStack), put **nginx** in front
   (Let's Encrypt + Basic Auth/Bearer), proxy to `http://127.0.0.1:8000/mcp` with
   `proxy_buffering off`.
   Security group: only **22** (your admin IP) and **443** public — **never expose
   port 8000**.
2. In Vibe Web: **Connectors → "Custom MCP server"**
   - Transport: **streamable HTTP**
   - URL: `https://<your-host>/mcp`
   - Auth: **Bearer** + token (from `.mcp-bearer-token` / your proxy credentials)
3. Verify: the connector appears in `list_my_connectors`, its tools in
   `list_connector_tools`.

> For quick tests only: a temporary tunnel from your local PC works too — then the
> server **must** have Bearer auth enabled (middleware `MCP_BEARER_TOKEN` in
> `openproject-mcp-http.py`). Tunnel URLs are public and change on every restart.

### Step 5 — Connect Mistral Vibe for VSCode (local, stdio)

Add to your MCP config:

```json
{
  "mcpServers": {
    "openproject": {
      "command": "uv",
      "args": ["run", "openproject-mcp-fastmcp.py"],
      "env": {
        "OPENPROJECT_URL": "https://<your-openproject-instance>",
        "OPENPROJECT_API_KEY": "<token-from-access-tokens>"
      }
    }
  }
}
```

All tools (`list_projects`, `list_work_packages`, …) are now available in the Vibe chat.

### Step 6 — Connect Claude Code / Claude Desktop (local, stdio)

Back up and edit the Claude config
(`%APPDATA%\Claude\claude_desktop_config.json` on Windows,
`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "openproject": {
      "command": "uv",
      "args": ["--directory", "/path/to/openproject-mcp-server", "run", "openproject-mcp-fastmcp.py"],
      "env": {
        "OPENPROJECT_URL": "https://<your-openproject-instance>",
        "OPENPROJECT_API_KEY": "<token-from-access-tokens>"
      }
    }
  }
}
```

Then **fully restart** Claude Code/Desktop and check the 🔌 MCP icon. Project-specific
agents, slash commands and hooks live in [`.claude/`](.claude/) — see
[`CLAUDE_CODE_GUIDE.md`](CLAUDE_CODE_GUIDE.md).

### Step 7 — Verify the integration (in this order)

1. `test_connection` → *API connection successful* + instance version
2. `check_permissions` → your user info
3. `list_projects` → your target project is visible
4. `list_work_packages(project_id=<id>, page_size=100)`
5. Epics/stories: `list_work_package_children(parent_id=<epic-id>, include_descendants=true)`

---

## 🔒 Security (mandatory)

- Limit the OpenProject API key to **minimal rights** and rotate it regularly.
- `.env`, `.mcp-bearer-token` and connector configs are gitignored — **never commit,
  share or paste them into chats**. Rotate any leaked token immediately.
- Never expose the MCP endpoint without **TLS + auth** (the server enforces none by
  itself, except the optional Bearer middleware).
- Use write tools (`create_*`, `update_work_package`, `delete_work_package`) only with
  an API key that has the corresponding project permissions.

---

## 🛠️ Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Connector error in Vibe Web | `127.0.0.1` instead of public URL | Enter the tunnel/VM URL including path `/mcp` |
| 401 | Bearer token wrong/rotated | Copy token exactly from `.mcp-bearer-token`, restart server |
| 403 on write access | API key lacks project rights | Check rights in OpenProject, run `check_permissions` |
| Tunnel URL dead | Tunnel restarted | Take the new URL from the log, update the connector |
| MCP server not showing in Claude | invalid JSON / wrong paths | Validate config, use absolute paths, restart completely |
| `list_time_entry_activities` → 404 | endpoint not available on all instances | Use hard-coded activity IDs 1–4 (Management/Specification/Development/Testing) |

---

## 📁 Repository layout

| Path | Purpose |
|---|---|
| `src/` | MCP server implementation (client, auth, tools) |
| `openproject-mcp-fastmcp.py` | stdio entry point (Vibe VSCode, Claude Code) |
| `openproject-mcp-http.py` | streamable-HTTP entry point (Vibe Web/Studio) |
| `openproject-mcp-sse.py` | SSE entry point |
| `test_*.py` | tool tests |
| `Dockerfile`, `pyproject.toml`, `requirements.txt` | packaging (fixed in this fork) |
| `README.md` | this step-by-step guide |
| `AGENT.md` | detailed Mistral (Studio / Vibe) integration guide (German) |
| `CLAUDE_CODE_SETUP.md` / `CLAUDE_CODE_GUIDE.md` | Claude Code setup + workflows |
| `.claude/` | Claude Code project config: agents, commands, hooks |

## 🙏 Credits

This project is an optimized fork of the original **openproject-mcp-server** by
[**AndyEverything**](https://github.com/AndyEverything) — thank you for the original work
and inspiration! The original project is community-driven (`contributions-welcome`, MIT)
and remains available at https://github.com/AndyEverything/openproject-mcp-server.
All changes in this fork are MIT-licensed as well.
