# Mistral MCP Servers — OpenProject & Trello Edition

A collection of **self-hosted MCP servers** (Python / FastMCP) optimized for
**Mistral** (Studio / Vibe Web & Vibe for VSCode) and **Claude** (Claude Code /
Claude Desktop) agents. More servers are added over time — currently:

| Server | Package / entry point | Purpose |
|---|---|---|
| **OpenProject** | `openproject_mcp/`, `openproject-mcp-*.py` | OpenProject API v3: projects, work packages, news, time entries, weekly reports |
| **Trello** | `apps/mcp/trello_mcp.py` | Boards/lists/cards by exact name: list, summarize, create, move, archive |

The OpenProject server is an optimized fork of
https://github.com/AndyEverything/openproject-mcp-server — see [Credits](#credits).

Detailed German guide for OpenProject + Mistral: [`AGENT.md`](AGENT.md). Claude-specific
docs: [`docs/CLAUDE_CODE_SETUP.md`](docs/CLAUDE_CODE_SETUP.md) and
[`docs/CLAUDE_CODE_GUIDE.md`](docs/CLAUDE_CODE_GUIDE.md).

## What's optimized in this fork

- **Fixed `Dockerfile`** — upstream `CMD` pointed to a non-existent `openproject-mcp.py`;
  now starts `openproject-mcp-fastmcp.py` and exposes port 8000
- **Complete `requirements.txt`** — upstream missed `fastmcp`, `pydantic`, `uvicorn`,
  `starlette` (only installable via `pyproject.toml`)
- **Removed the 138 KB legacy monolith** (`openproject-mcp.legacy.py`) — dead code
- **Cleaner structure** — package renamed `src` → `openproject_mcp`, tests in `tests/`,
  guides in `docs/`
- **Packaging metadata** — real author, repo URLs (`Repository` / `Upstream`), version bump
- **Step-by-step agent setup** (below) for Mistral Vibe and Claude Code

---

## OpenProject MCP — step-by-step setup

### Prerequisites

- An **OpenProject instance** (cloud or self-hosted) and an **API key**
- **Python 3.10+** and [uv](https://docs.astral.sh/uv/) (or plain pip)
- A **Mistral account** (Studio / Vibe) *or* **Claude Code / Claude Desktop** installed
- For Mistral Vibe **Web** (cloud): a server with a **public HTTPS URL** (e.g. a VM with
  nginx + Let's Encrypt) — see Step 4

### Step 1 — Clone and set up this repository

```bash
git clone https://github.com/GManSudy/mistral-mcp-server.git
cd mistral-mcp-server
uv sync          # or: pip install -r requirements.txt
```

### Step 2 — Configure the OpenProject server

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

### Step 3 — Start the OpenProject server (pick one transport)

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
      "args": ["--directory", "/path/to/mistral-mcp-server", "run", "openproject-mcp-fastmcp.py"],
      "env": {
        "OPENPROJECT_URL": "https://<your-openproject-instance>",
        "OPENPROJECT_API_KEY": "<token-from-access-tokens>"
      }
    }
  }
}
```

Then **fully restart** Claude Code/Desktop and check the MCP icon in the status bar.
Project-specific agents, slash commands and hooks live in [`.claude/`](.claude/) — see
[`docs/CLAUDE_CODE_GUIDE.md`](docs/CLAUDE_CODE_GUIDE.md).

### Step 7 — Verify the integration (in this order)

1. `test_connection` → *API connection successful* + instance version
2. `check_permissions` → your user info
3. `list_projects` → your target project is visible
4. `list_work_packages(project_id=<id>, page_size=100)`
5. Epics/stories: `list_work_package_children(parent_id=<epic-id>, include_descendants=true)`

---

## Trello MCP (self-hosted, FastMCP)

Standalone **Trello MCP server** in `apps/mcp/`, reusing the API client from
`apps/worker`. Boards/lists/cards are resolved by **exact name** (emojis included),
same semantics as the write-queue.

**Tools:** `list_boards`, `board_summary(board)`, `create_card(board, list, name, desc?)`,
`move_card(board, card, list)`, `archive_card(board, card)`

**Setup:**

```bash
cp apps/mcp/env_example.txt .env   # TRELLO_API_KEY + TRELLO_TOKEN eintragen
pip install -r apps/mcp/requirements.txt
python apps/mcp/trello_mcp.py                 # stdio -> Vibe for VSCode / Claude Code
python apps/mcp/trello_mcp.py --http          # HTTP POST /mcp on :8000 (for Vibe Web)
```

Token erzeugen: trello.com/power-ups/admin → App → „manually generate a token".

**Docker (for Vibe Web: public HTTPS URL, nginx + Basic Auth in front):**

```bash
docker build -f deploy/docker/Dockerfile.mcp -t trello-mcp .
docker run -p 8000:8000 --env-file .env trello-mcp
```

**VSCode (Vibe) — `.vscode/mcp.json`** (see `apps/mcp/mcp.example.json`):

```json
{
  "servers": {
    "trello": {
      "command": "python",
      "args": ["apps/mcp/trello_mcp.py"],
      "env": { "TRELLO_API_KEY": "...", "TRELLO_TOKEN": "..." }
    }
  }
}
```

---

## Security (mandatory)

- Limit API keys (OpenProject, Trello) to **minimal rights** and rotate them regularly.
- `.env`, `.mcp-bearer-token` and connector configs are gitignored — **never commit,
  share or paste them into chats**. Rotate any leaked token immediately.
- Never expose an MCP endpoint without **TLS + auth** (the servers enforce none by
  themselves, except the optional Bearer middleware).
- Use write tools (`create_*`, `update_*`, `move_card`, `archive_card`, …) only with
  credentials that have the corresponding permissions.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Connector error in Vibe Web | `127.0.0.1` instead of public URL | Enter the tunnel/VM URL including path `/mcp` |
| 401 | Bearer token wrong/rotated | Copy token exactly from `.mcp-bearer-token`, restart server |
| 403 on write access | API key lacks project rights | Check rights in OpenProject/Trello, run `check_permissions` |
| Tunnel URL dead | Tunnel restarted | Take the new URL from the log, update the connector |
| MCP server not showing in Claude | invalid JSON / wrong paths | Validate config, use absolute paths, restart completely |
| `list_time_entry_activities` → 404 | endpoint not available on all instances | Use hard-coded activity IDs 1–4 (Management/Specification/Development/Testing) |
| Trello: board/list/card not found | name mismatch (incl. emojis) | Use the exact name, check with `list_boards` / `board_summary` |

---

## Repository layout

```
mistral-mcp-server/
├── README.md                  this guide
├── AGENT.md                   detailed OpenProject + Mistral (Studio/Vibe) guide (German)
├── pyproject.toml             packaging metadata for the OpenProject server
├── requirements.txt           complete dependency list (OpenProject server)
├── uv.lock                    lockfile
├── Dockerfile                 OpenProject server container (CMD + EXPOSE 8000)
├── env_example.txt            OpenProject .env template
├── openproject-mcp-fastmcp.py OpenProject stdio entry point
├── openproject-mcp-http.py    OpenProject streamable-HTTP entry point
├── openproject-mcp-sse.py     OpenProject SSE entry point
├── openproject_mcp/           OpenProject server package (client, auth, tools, utils)
├── apps/mcp/                  Trello MCP server (trello_mcp.py) + requirements + example config
├── apps/worker/src/worker/    shared Trello API client (trello_client.py)
├── deploy/docker/             Dockerfile.mcp for the Trello server
├── scripts/                   install helper (install_mcp.ps1)
├── tests/                     OpenProject tool tests (test_*.py)
├── docs/                      guides: Claude Code setup/guide, news tools
└── .claude/                   Claude Code project config (agents, commands, hooks)
```

## Credits

The **OpenProject MCP server** in this repo is an optimized fork of the original
**openproject-mcp-server** by [**AndyEverything**](https://github.com/AndyEverything) —
thank you for the original work and inspiration! The original project is
community-driven (`contributions-welcome`, MIT) and remains available at
https://github.com/AndyEverything/openproject-mcp-server.
The **Trello MCP server** (`apps/`) is original work for this repo.
Everything here is MIT-licensed.
