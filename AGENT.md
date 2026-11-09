# AGENT.md — Mistral (Studio / Vibe) an OpenProject anbinden

Anleitung für Agents und Contributor: wie dieser MCP-Server (`openproject-mcp-server`,
FastMCP, Python) mit Mistral Studio / Mistral Vibe (Web & VSCode) verbunden wird. Dieser Fork enthält eine optimierte Fassung des Server-Codes; das Original stammt von `AndyEverything/openproject-mcp-server` (Credits siehe README).

## Schnellstart: Integration mit Mistral Vibe (Web & VSCode)

Analog zur Claude-Integration im README — zwei Wege:

### Vibe Web (Studio): Custom-MCP-Connector
1. Server mit erreichbarer HTTPS-URL bereitstellen (siehe „Variante B", Schritt 2)
2. Vibe Web → Connectors → „Benutzerdefinierter MCP-Server"
   - Transport: **streamable HTTP**
   - URL: `https://<host>/mcp`
   - Auth: **Bearer** + Token aus `.mcp-bearer-token`
3. Verifizieren: `test_connection`, dann `list_projects`

### Vibe VSCode (lokal): stdio-Config
```json
{
  "mcpServers": {
    "openproject": {
      "command": "uv",
      "args": ["run", "openproject-mcp-fastmcp.py"],
      "env": {
        "OPENPROJECT_URL": "https://<deine-openproject-instanz>",
        "OPENPROJECT_API_KEY": "<token-aus-access-tokens>"
      }
    }
  }
}
```
Danach stehen im Vibe-Chat alle Tools bereit (`list_projects`, `list_work_packages`, …).

## Optionen im Überblick

| Option | Voraussetzung | Aufwand |
|---|---|---|
| A. Offizieller OpenProject-MCP-Server | OpenProject >= 17.2, Enterprise-Add-on ab Plan Professional | gering |
| B. Dieser Custom-MCP-Server als Connector | Community/self-hosted OpenProject | mittel |
| C. Direkt REST API v3 (Webhooks/HTTP) | nur punktuelle Automationen | gering |

Empfehlung: A wenn verfügbar, sonst B.

## Variante B: Dieser Server als MCP-Connector

### 1. Server lokal aufsetzen
```bash
cp env_example.txt .env     # OPENPROJECT_URL + OPENPROJECT_API_KEY eintragen
uv sync                      # oder: pip install .
```
- API-Key in OpenProject: Avatar → My account → Access tokens → + Add
- Auth gegen OpenProject: `Authorization: Basic base64("apikey:" + KEY)`
  (`src/client.py`). `Authorization: ApiKey <token>` wird von OpenProject **abgelehnt**.
- HTTP-Modus (für Studio/Vibe Web): `uv run openproject-mcp-http.py`
  (Default `0.0.0.0:8000`, Endpunkt `POST /mcp`, streamable HTTP)
- stdio-Modus (für lokale MCP-Clients wie Vibe VSCode / Claude Desktop):
  `uv run openproject-mcp-fastmcp.py`
- Lokaler Smoke-Test: `MCP_HTTP_HOST=127.0.0.1` setzen, dann MCP-`initialize`
  gegen `http://127.0.0.1:8000/mcp` → erwartet HTTP 200 mit Session-ID.

### 2. Endpunkt für Mistral Cloud erreichbar machen
Studio/Vibe Web laufen in der Cloud → der MCP-Endpunkt braucht eine **öffentlich
erreichbare HTTPS-URL mit Auth davor**:
- Empfohlen: VM (z. B. OpenStack) mit nginx (Let's Encrypt + Basic Auth/Bearer),
  Proxy auf `http://127.0.0.1:8000/mcp` mit `proxy_buffering off`.
  Security Group: nur 22 (Admin-IP) + 443 öffentlich; **Port 8000 nie freigeben**.
  Details siehe `DEPLOY-OPENSTACK.md`.
- Nur für Tests: temporärer Tunnel vom lokalen PC — dann **zwingend** Bearer-Auth
  im Server (Middleware `MCP_BEARER_TOKEN` in `openproject-mcp-http.py`).
  Quick-Tunnel-URLs sind öffentlich und wechseln bei jedem Neustart.

### 3. Connector in Mistral Studio / Vibe Web anlegen
- Connectors → „Benutzerdefinierter MCP-Server" / „Custom MCP server"
- Transport: **streamable HTTP**, URL: `https://<host>/mcp`
- Auth: Bearer-Token (aus `.mcp-bearer-token`) bzw. Proxy-Credentials
- Danach: Connector in `list_my_connectors` sichtbar, Tools in `list_connector_tools`

### 4. Verifizieren (Reihenfolge)
1. `test_connection` → API connection successful
2. `list_projects` → Zielprojekt sichtbar
3. `list_work_packages(project_id=<id>, page_size=100)`
4. Epics/Stories: `list_work_package_children(parent_id=<epic-id>, include_descendants=true)`

### 5. Vibe (VSCode) lokal via stdio
```json
{
  "mcpServers": {
    "openproject": {
      "command": "uv",
      "args": ["run", "openproject-mcp-fastmcp.py"],
      "env": {
        "OPENPROJECT_URL": "https://…",
        "OPENPROJECT_API_KEY": "…"
      }
    }
  }
}
```

## Sicherheit (Pflicht)

- OpenProject-API-Key auf minimale Rechte begrenzen, regelmäßig rotieren.
- `.env`, `.mcp-bearer-token`, Connector-Configs sind gitignored und dürfen **nie
  committed, geteilt oder an Chats angehängt** werden. Gefundene/leakte Tokens
  sofort rotieren (neuer Wert in `.mcp-bearer-token`, Server neu starten,
  Connector-Header aktualisieren).
- MCP-Endpunkt nie ohne TLS + Auth exponieren — der Server erzwingt selbst keine
  Auth (Ausnahme: eigene Bearer-Middleware, s. o.).
- Schreib-Tools (`update_work_package`, `delete_work_package`, `create_*`) nur mit
  entsprechend berechtigten API-Key verwenden.

## Troubleshooting

| Symptom | Ursache | Lösung |
|---|---|---|
| Connector-Fehler in Vibe Web | `127.0.0.1` statt öffentlicher URL | Tunnel-/VM-URL inkl. Pfad `/mcp` eintragen |
| 401 | Bearer-Token falsch/rotiert | Token exakt aus `.mcp-bearer-token` übernehmen, Server neu starten |
| 403 bei Schreibzugriff | API-Key ohne Projekt-Rechte | Rechte in OpenProject prüfen, `check_permissions` ausführen |
| Tunnel-URL tot | Tunnel neu gestartet | neue URL aus Log übernehmen, Connector aktualisieren |
| `list_time_entry_activities` → 404 | Endpunkt nicht auf allen Instanzen | Aktivität-IDs 1–4 (Management/Specification/Development/Testing) hart codiert nutzen |

## Nützliche Tool-Beispiele

```
list_work_packages(project_id=58, active_only=false, page_size=100)
search_work_packages(query="Orchestrator", project_id=58)
list_work_package_children(parent_id=3097, include_descendants=true)
get_work_package(work_package_id=3097)
update_work_package(input={work_package_id: 3097, percentage_done: 50})
```

## Docker-Deployment (korrigiert)

Das ursprüngliche `Dockerfile` war defekt (CMD zeigte auf nicht existierende Datei,
`requirements.txt` unvollständig). Korrigierte Fassung + `docker-compose.yml`
liegen in diesem Branch bzw. siehe `DEPLOY-OPENSTACK.md` für das VM-Runbook.
