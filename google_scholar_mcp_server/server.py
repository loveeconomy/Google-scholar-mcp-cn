from __future__ import annotations

import asyncio
import os
from typing import Any, Literal

from mcp.server.fastmcp import FastMCP

from .client import GoogleScholarClient

SERVER_INSTRUCTIONS = (
    "Search Google Scholar publications and author profiles. "
    "This server depends on Google Scholar availability and may require a proxy "
    "in regions where Scholar blocks automated requests."
)

app = FastMCP(
    name="google-scholar",
    instructions=SERVER_INSTRUCTIONS,
)
mcp = app


def _client() -> GoogleScholarClient:
    return GoogleScholarClient()


def _tool_timeout_sec() -> int:
    return max(5, int(os.getenv("GOOGLE_SCHOLAR_TOOL_TIMEOUT_SEC", "15")))


@app.tool()
async def search_google_scholar_key_words(
    query: str,
    num_results: int = 5,
) -> list[dict[str, Any]]:
    """Search Google Scholar publications by keywords."""
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(_client().search_keywords, query, num_results),
            timeout=_tool_timeout_sec(),
        )
    except TimeoutError as exc:
        raise RuntimeError("Keyword search timed out while waiting for Google Scholar.") from exc


@app.tool()
async def search_google_scholar_advanced(
    all_words: str = "",
    exact_phrase: str = "",
    any_words: str = "",
    exclude_words: str = "",
    search_in: str = "anywhere",
    author: str = "",
    publication: str = "",
    start_year: int | None = None,
    end_year: int | None = None,
    num_results: int = 5,
) -> list[dict[str, Any]]:
    """Search Google Scholar publications with advanced search filters."""
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(
                _client().search_advanced,
                all_words,
                exact_phrase,
                any_words,
                exclude_words,
                search_in,
                author,
                publication,
                start_year,
                end_year,
                num_results,
            ),
            timeout=_tool_timeout_sec(),
        )
    except TimeoutError as exc:
        raise RuntimeError("Advanced search timed out while waiting for Google Scholar.") from exc


@app.tool()
async def get_author_info(author_name: str) -> dict[str, Any]:
    """Fetch an author's public Google Scholar profile."""
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(_client().get_author_info, author_name),
            timeout=_tool_timeout_sec(),
        )
    except TimeoutError as exc:
        raise RuntimeError("Author lookup timed out while waiting for Google Scholar.") from exc


def main() -> None:
    transport = os.getenv("GOOGLE_SCHOLAR_TRANSPORT", "stdio").strip() or "stdio"
    valid_transports: tuple[Literal["stdio"], Literal["sse"], Literal["streamable-http"]] = (
        "stdio",
        "sse",
        "streamable-http",
    )
    if transport not in valid_transports:
        raise ValueError(
            "GOOGLE_SCHOLAR_TRANSPORT must be one of: stdio, sse, streamable-http."
        )

    app.run(transport=transport)
