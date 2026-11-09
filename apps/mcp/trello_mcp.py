#!/usr/bin/env python3
"""Self-hosted Trello MCP server (FastMCP).

Transports:
  stdio (default):   python apps/mcp/trello_mcp.py
  HTTP:              python apps/mcp/trello_mcp.py --http [--port 8000]  -> POST /mcp

Credentials via environment: TRELLO_API_KEY, TRELLO_TOKEN.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "worker", "src"))

from common import create_server, load_env, run_server
from worker.workflows.trello_client import (
    TrelloError,
    trello_get,
    trello_post,
    trello_put,
)

load_env()

mcp = create_server("trello")


async def _resolve_board_id(board: str) -> str:
    boards = await trello_get("/members/me/boards", {"fields": "id,name"})
    for b in boards:
        if b["name"] == board:
            return b["id"]
    raise TrelloError(f"Board '{board}' not found.")


async def _resolve_list_id(board_id: str, list_name: str) -> str:
    lists = await trello_get(f"/boards/{board_id}/lists", {"fields": "name"})
    for lst in lists:
        if lst["name"] == list_name:
            return lst["id"]
    raise TrelloError(f"List '{list_name}' not found in board.")


async def _resolve_card_id(board_id: str, card: str) -> str:
    cards = await trello_get(f"/boards/{board_id}/cards", {"fields": "name"})
    for c in cards:
        if c["name"] == card:
            return c["id"]
    raise TrelloError(f"Card '{card}' not found in board.")


@mcp.tool()
async def list_boards() -> list[dict]:
    """List all Trello boards of the authorized member (id, name, url)."""
    boards = await trello_get("/members/me/boards", {"fields": "id,name,url"})
    return [{"id": b["id"], "name": b["name"], "url": b.get("url")} for b in boards]


@mcp.tool()
async def board_summary(board: str) -> dict:
    """Lists and open cards of one board (board resolved by exact name)."""
    board_id = await _resolve_board_id(board)
    data = await trello_get(
        f"/boards/{board_id}",
        {
            "fields": "name",
            "lists": "open",
            "list_fields": "name",
            "cards": "open",
            "card_fields": "name,due,labels,idList",
        },
    )
    lists = {
        lst["id"]: {"id": lst["id"], "name": lst["name"], "cards": []}
        for lst in data.get("lists", [])
    }
    for card in data.get("cards", []):
        lists.setdefault(
            card["idList"], {"id": card["idList"], "name": "?", "cards": []}
        )["cards"].append(
            {
                "id": card["id"],
                "name": card["name"],
                "due": card.get("due"),
                "labels": [l["name"] for l in card.get("labels", [])],
            }
        )
    return {"board_id": board_id, "board_name": data["name"], "lists": list(lists.values())}


@mcp.tool()
async def create_card(board: str, list: str, name: str, desc: str = "") -> dict:
    """Create a card in a list (names resolved exactly, emojis included)."""
    board_id = await _resolve_board_id(board)
    list_id = await _resolve_list_id(board_id, list)
    card = await trello_post("/cards", {"idList": list_id, "name": name, "desc": desc})
    return {"id": card["id"], "name": card["name"], "list": list}


@mcp.tool()
async def move_card(board: str, card: str, list: str) -> dict:
    """Move a card to another list in the same board."""
    board_id = await _resolve_board_id(board)
    card_id = await _resolve_card_id(board_id, card)
    list_id = await _resolve_list_id(board_id, list)
    await trello_put(f"/cards/{card_id}", {"idList": list_id})
    return {"card": card, "list": list}


@mcp.tool()
async def archive_card(board: str, card: str) -> dict:
    """Archive (close) a card."""
    board_id = await _resolve_board_id(board)
    card_id = await _resolve_card_id(board_id, card)
    await trello_put(f"/cards/{card_id}", {"closed": "true"})
    return {"card": card, "archived": True}


if __name__ == "__main__":
    run_server(mcp, "Trello MCP server")
