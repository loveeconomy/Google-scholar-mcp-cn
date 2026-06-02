from google_scholar_mcp_server.server import (
    get_author_info,
    main,
    mcp,
    search_google_scholar_advanced,
    search_google_scholar_key_words,
)

__all__ = [
    "mcp",
    "main",
    "search_google_scholar_key_words",
    "search_google_scholar_advanced",
    "get_author_info",
]


if __name__ == "__main__":
    main()
