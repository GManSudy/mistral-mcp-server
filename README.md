# MCP Servers for Mistral Vibe

**Self-hosted MCP servers** (Python / FastMCP) for **Mistral Studio / Vibe Web** and
**Vibe for VSCode**. One repo, one config, one Docker image — every MCP server here
deploys the same way, and new ones can be added without changing the setup.

Currently included:

| Server | Entry point | Purpose |
|---|---|---|
| **OpenProject** | `openproject-mcp-*.py` | OpenProject API v3: projects, work packages, news, time entries, weekly reports |
| **Trello** | `apps/mcp/trello_mcp.py` | Boards/lists/cards by exact name: list, summarize, create, move, archive |

Detailed German guide for OpenProject + Mistral: [`AGENT.md`](AGENT.md).

---

## Quickstart (all servers, unified)

```bash
git clone https://github.com/GManSudy/mistral-mcp-server.git
cd mistral-mcp-server
cp env_example.txt .env        # fill in OPENPROJECT_* and/or TRELLO_*
uv sync                        # or: pip install -r requirements.txt
```

`env_example.txt` / `.env` is shared by all servers — each server reads only its own
variables, so you can configure one or many.

### Run a server locally (stdio — for Vibe VSCode)

```bash
uv run openproject-mcp-fastmcp.py     # OpenProject, stdio
python apps/mcp/trello_mcp.py         # Trello, stdio
```

Vibe VSCode `mcpServers` config (example OpenProject):

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

### Run a server as HTTP (for Vibe Web / Studio — needs public HTTPS, see below)

```bash
uv run openproject-mcp-http.py                 # POST /mcp on :8000
python apps/mcp/trello_mcp.py --http --port 8001
```

### Deploy everything with Docker (one command)

```bash
cp env_example.txt .env
docker compose -f deploy/docker/docker-compose.yml up --build
# OpenProject MCP: http://localhost:8000/mcp
# Trello MCP:      http://localhost:8001/mcp
```

The single `Dockerfile` builds one image for **all** servers; select the server via
environment variables:

```bash
docker build -t mcp-servers .
docker run -p 8000:8000 --env-file .env mcp-servers                                  # OpenProject HTTP (default)
docker run -p 8001:8000 --env-file .env -e MCP_ENTRYPOINT=apps/mcp/trello_mcp.py \
  -e MCP_ARGS="--http --port 8000" mcp-servers                                       # Trello HTTP
```

---

## Mistral Vibe Web (Studio) — expose an MCP endpoint publicly

Studio/Vibe Web run in the cloud, so the MCP endpoint needs a **publicly reachable
HTTPS URL with auth in front**:

1. Run the server on a VM (e.g. OpenStack), put **nginx** in front
   (Let's Encrypt + Basic Auth/Bearer), proxy to `http://127.0.0.1:8000/mcp` with
   `proxy_buffering off`. Security group: only **22** (your admin IP) and **443**
   public — **never expose port 8000**.
2. In Vibe Web: **Connectors → "Custom MCP server"**
   - Transport: **streamable HTTP**
   - URL: `https://<your-host>/mcp`
   - Auth: **Bearer** + token (from `.mcp-bearer-token` / your proxy credentials)
3. Verify: the connector appears in `list_my_connectors`, its tools in
   `list_connector_tools`.

> For quick tests only: a temporary tunnel from your local PC works too — then the
> server **must** have Bearer auth enabled (middleware `MCP_BEARER_TOKEN` in
> `openproject-mcp-http.py`). Tunnel URLs are public and change on every restart.

---

## Server: OpenProject

**Setup:** `cp env_example.txt .env` and fill in `OPENPROJECT_URL` + `OPENPROJECT_API_KEY`
(OpenProject: Avatar → *My account* → *Access tokens* → *+ Add*). The server
authenticates with `Authorization: Basic base64("apikey:" + KEY)` —
`Authorization: ApiKey <token>` is **rejected** by OpenProject.

**Verify (in this order):**

1. `test_connection` → *API connection successful* + instance version
2. `check_permissions` → your user info
3. `list_projects` → your target project is visible
4. `list_work_packages(project_id=<id>, page_size=100)`
5. Epics/stories: `list_work_package_children(parent_id=<epic-id>, include_descendants=true)`

Local smoke test (HTTP mode): set `MCP_HTTP_HOST=127.0.0.1`, then send an MCP
`initialize` request to `http://127.0.0.1:8000/mcp` → expect HTTP 200 with a session ID.

## Server: Trello

**Setup:** fill in `TRELLO_API_KEY` + `TRELLO_TOKEN` in `.env`
(token: trello.com/power-ups/admin → App → „manually generate a token").

**Tools:** `list_boards`, `board_summary(board)`, `create_card(board, list, name, desc?)`,
`move_card(board, card, list)`, `archive_card(board, card)`

Boards/lists/cards are resolved by **exact name** (emojis included).

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
| 403 on write access | API key lacks rights | Check rights in OpenProject/Trello, run `check_permissions` |
| Tunnel URL dead | Tunnel restarted | Take the new URL from the log, update the connector |
| MCP server not showing in Vibe VSCode | invalid JSON / wrong paths | Validate config, use absolute paths, restart completely |
| `list_time_entry_activities` → 404 | endpoint not available on all instances | Use hard-coded activity IDs 1–4 (Management/Specification/Development/Testing) |
| Trello: board/list/card not found | name mismatch (incl. emojis) | Use the exact name, check with `list_boards` / `board_summary` |

---

## Repository layout

```
mistral-mcp-server/
├── README.md                  this guide
├── AGENT.md                   detailed OpenProject + Mistral (Studio/Vibe) guide (German)
├── pyproject.toml             packaging metadata for the OpenProject server
├── requirements.txt           unified dependency list (ALL servers)
├── uv.lock                    lockfile
├── env_example.txt            unified .env template (OpenProject + Trello + shared)
├── Dockerfile                 unified image for ALL servers (MCP_ENTRYPOINT/MCP_ARGS)
├── deploy/docker/
│   └── docker-compose.yml     deploys all servers at once
├── openproject-mcp-fastmcp.py OpenProject stdio entry point
├── openproject-mcp-http.py    OpenProject streamable-HTTP entry point
├── openproject-mcp-sse.py     OpenProject SSE entry point
├── openproject_mcp/           OpenProject server package (client, auth, tools, utils)
├── apps/mcp/
│   ├── common.py              shared boilerplate: .env loading, CLI (--http/--port), server factory
│   ├── server_template.py     copy this for a new server
│   ├── trello_mcp.py          Trello MCP server (stdio + --http)
│   └── mcp.example.json       Vibe VSCode config example (all servers)
├── apps/worker/src/worker/    shared Trello API client (trello_client.py)
├── tests/                     OpenProject tool tests (test_*.py)
└── docs/                      guides (e.g. news tools)
```

## Adding another MCP server

All servers live in `apps/mcp/` and share the same boilerplate (`apps/mcp/common.py`):
unified `.env` loading, one CLI (`stdio` by default, `--http [--host] [--port]`).

1. `cp apps/mcp/server_template.py apps/mcp/<name>_mcp.py` and fill in your tools.
2. Read credentials from the unified `.env` (add a section to `env_example.txt`).
3. Run: `python apps/mcp/<name>_mcp.py [--http]`.
4. Deploy: no Docker changes needed — `MCP_ENTRYPOINT=apps/mcp/<name>_mcp.py`
   (+ `MCP_ARGS="--http --port 8000"`), or add a service to
   `deploy/docker/docker-compose.yml`.
5. Add an entry to `apps/mcp/mcp.example.json` for Vibe VSCode.

## Credits

The **OpenProject MCP server** in this repo is an optimized fork of the original
**openproject-mcp-server** by [**AndyEverything**](https://github.com/AndyEverything) —
thank you for the original work and inspiration! The original project is
community-driven (`contributions-welcome`, MIT) and remains available at
https://github.com/AndyEverything/openproject-mcp-server.
The **Trello MCP server** (`apps/`) is original work for this repo.
Everything here is MIT-licensed.
