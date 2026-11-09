"""Trello API client for workflow activities and the MCP server.

Reads credentials from environment variables:
- TRELLO_API_KEY
- TRELLO_TOKEN
"""

import os

import httpx

TRELLO_API_BASE = "https://api.trello.com/1"


class TrelloError(Exception):
    """Raised when the Trello API answers with an error."""


def _credentials() -> dict[str, str]:
    key = os.environ.get("TRELLO_API_KEY", "")
    token = os.environ.get("TRELLO_TOKEN", "")
    if not key or not token:
        raise TrelloError(
            "Missing Trello credentials: set TRELLO_API_KEY and TRELLO_TOKEN."
        )
    return {"key": key, "token": token}


async def _request(method: str, path: str, params: dict | None = None) -> object:
    query = _credentials()
    if params:
        query.update(params)
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.request(
            method, f"{TRELLO_API_BASE}{path}", params=query
        )
        if response.status_code >= 400:
            raise TrelloError(
                f"Trello API error {response.status_code} for {method} {path}: "
                f"{response.text[:300]}"
            )
        return response.json()


async def trello_get(path: str, params: dict | None = None) -> object:
    return await _request("GET", path, params)


async def trello_post(path: str, params: dict | None = None) -> object:
    return await _request("POST", path, params)


async def trello_put(path: str, params: dict | None = None) -> object:
    return await _request("PUT", path, params)
