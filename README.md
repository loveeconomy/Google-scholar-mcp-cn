# Google Scholar MCP Server

Expose Google Scholar search and author lookup through the Model Context Protocol (MCP).

This project provides a small MCP server for AI assistants that need to:

- search Google Scholar by keywords
- apply author and year filters
- fetch public author profile information

## Status

The server uses a Scholar mirror by default:

- `https://scholar.lanfanshu.cn`

You can override it with:

- `GOOGLE_SCHOLAR_BASE_URL`

If the mirror is slow or blocked, configure a proxy with:

- `GOOGLE_SCHOLAR_HTTP_PROXY`
- `GOOGLE_SCHOLAR_HTTPS_PROXY`

Other useful environment variables:

- `GOOGLE_SCHOLAR_TIMEOUT_SEC` (default: `8`)
- `GOOGLE_SCHOLAR_AUTHOR_PUBLICATION_LIMIT` (default: `5`)
- `GOOGLE_SCHOLAR_TRANSPORT` (`stdio`, `sse`, or `streamable-http`; default: `stdio`)

## Installation

```bash
git clone https://github.com/JackKuo666/Google-Scholar-MCP-Server.git
cd Google-Scholar-MCP-Server
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

On Windows:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run

Start the MCP server in stdio mode:

```bash
python -m google_scholar_mcp_server
```

The legacy entrypoint still works:

```bash
python google_scholar_server.py
```

## MCP Tools

### `search_google_scholar_key_words`

Parameters:

- `query`: search string
- `num_results`: integer from `1` to `20`

Returns a list of publication objects:

```json
[
  {
    "title": "Example Paper",
    "authors": "Alice, Bob",
    "abstract": "Short summary",
    "year": "2024",
    "venue": "NeurIPS",
    "citations": 12,
    "publication_url": "https://example.com",
    "scholar_url": "https://scholar.google.com/...",
    "source": "scholarly"
  }
]
```

### `search_google_scholar_advanced`

Parameters:

- `all_words`: words that must all appear
- `exact_phrase`: exact phrase that must appear
- `any_words`: at least one of these words should appear
- `exclude_words`: words to exclude
- `search_in`: `anywhere` or `title`
- `author`: optional author filter
- `publication`: optional journal or publication filter
- `start_year`: optional start year
- `end_year`: optional end year
- `num_results`: integer from `1` to `20`

Example:

```json
{
  "all_words": "预测",
  "exact_phrase": "系统工程",
  "any_words": "",
  "exclude_words": "",
  "search_in": "anywhere",
  "author": "",
  "publication": "系统工程",
  "start_year": 2025,
  "end_year": 2025,
  "num_results": 3
}
```

### `get_author_info`

Parameters:

- `author_name`: author display name

Returns:

```json
{
  "name": "Geoffrey Hinton",
  "affiliation": "University of Toronto",
  "interests": ["deep learning"],
  "cited_by": 123456,
  "scholar_id": "abc123",
  "profile_url": "https://scholar.lanfanshu.cn/citations?hl=zh-CN&user=abc123",
  "email_verification": "verified email at example.edu",
  "publications": []
}
```

Note: on the mirror currently used here, `get_author_info` is parsed from the author search results page. That means author summary fields are available, but detailed publication lists may be empty.

## Claude Desktop Example

```json
{
  "mcpServers": {
    "google-scholar": {
      "command": "C:\\Users\\YOUR_USER\\Desktop\\search\\Google-Scholar-MCP-Server\\venv\\Scripts\\python.exe",
      "args": [
        "-m",
        "google_scholar_mcp_server"
      ]
    }
  }
}
```

## Development

Run unit tests:

```bash
python -m unittest discover -s tests -v
```

## Project Layout

- `google_scholar_mcp_server/client.py`: Google Scholar access and normalization
- `google_scholar_mcp_server/server.py`: FastMCP tool registration and entrypoint
- `google_scholar_server.py`: legacy compatibility entrypoint
- `google_scholar_web_search.py`: legacy compatibility wrapper

## License

MIT
