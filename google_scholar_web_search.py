from google_scholar_mcp_server.client import GoogleScholarClient


def google_scholar_search(query: str, num_results: int = 5) -> list[dict]:
    return GoogleScholarClient().search_keywords(query, num_results)


def advanced_google_scholar_search(
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
) -> list[dict]:
    return GoogleScholarClient().search_advanced(
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
    )
