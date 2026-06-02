from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qs, urlencode, urljoin, urlparse

import requests
from bs4 import BeautifulSoup


class ScholarServiceError(RuntimeError):
    """Raised when the configured scholar mirror cannot be reached reliably."""


@dataclass(slots=True)
class ScholarConfig:
    base_url: str = "https://scholar.lanfanshu.cn"
    timeout_sec: int = 8
    author_publication_limit: int = 5
    http_proxy: str | None = None
    https_proxy: str | None = None

    @classmethod
    def from_env(cls) -> "ScholarConfig":
        return cls(
            base_url=(os.getenv("GOOGLE_SCHOLAR_BASE_URL", "https://scholar.lanfanshu.cn").rstrip("/")),
            timeout_sec=max(1, int(os.getenv("GOOGLE_SCHOLAR_TIMEOUT_SEC", "8"))),
            author_publication_limit=max(
                1, int(os.getenv("GOOGLE_SCHOLAR_AUTHOR_PUBLICATION_LIMIT", "5"))
            ),
            http_proxy=os.getenv("GOOGLE_SCHOLAR_HTTP_PROXY"),
            https_proxy=os.getenv("GOOGLE_SCHOLAR_HTTPS_PROXY"),
        )


class GoogleScholarClient:
    _USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    )

    def __init__(self, config: ScholarConfig | None = None) -> None:
        self.config = config or ScholarConfig.from_env()

    def search_keywords(self, query: str, num_results: int = 5) -> list[dict[str, Any]]:
        query = self._validate_query(query)
        num_results = self._validate_num_results(num_results)
        params = {"hl": "en", "q": query}
        soup = self._get_soup("/scholar", params)
        return self._parse_publication_results(soup, num_results)

    def search_advanced(
        self,
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
        num_results = self._validate_num_results(num_results)
        year_low, year_high = self._normalize_year_range(start_year, end_year)

        params: dict[str, str] = {"hl": "en"}
        if all_words.strip():
            params["as_q"] = all_words.strip()
        if exact_phrase.strip():
            params["as_epq"] = exact_phrase.strip()
        if any_words.strip():
            params["as_oq"] = any_words.strip()
        if exclude_words.strip():
            params["as_eq"] = exclude_words.strip()
        if author.strip():
            params["as_sauthors"] = author.strip()
        if publication.strip():
            params["as_publication"] = publication.strip()
        params["as_occt"] = self._normalize_search_in(search_in)
        if year_low is not None:
            params["as_ylo"] = str(year_low)
        if year_high is not None:
            params["as_yhi"] = str(year_high)
        if not any(
            key in params
            for key in ("as_q", "as_epq", "as_oq", "as_eq", "as_sauthors", "as_publication")
        ):
            raise ValueError(
                "At least one advanced search field must be provided."
            )

        soup = self._get_soup("/scholar", params)
        return self._parse_publication_results(soup, num_results)

    def get_author_info(self, author_name: str) -> dict[str, Any]:
        author_name = self._validate_query(author_name, field_name="author_name")
        soup = self._get_soup(
            "/citations",
            {"hl": "en", "view_op": "search_authors", "mauthors": author_name},
        )

        row = soup.find("div", class_="gsc_1usr")
        if row is None:
            raise ScholarServiceError(f"No scholar author found for '{author_name}'.")

        name_link = row.select_one("h3.gs_ai_name a")
        citation_text = self._text_or_empty(row.find("div", class_="gs_ai_cby"))
        return {
            "name": self._text_or_empty(name_link),
            "affiliation": self._text_or_empty(row.find("div", class_="gs_ai_aff")),
            "interests": [
                self._text_or_empty(tag)
                for tag in row.select("a.gs_ai_one_int")
                if self._text_or_empty(tag)
            ],
            "cited_by": self._extract_first_int(citation_text),
            "scholar_id": self._extract_user_id(name_link.get("href", "") if name_link else ""),
            "profile_url": self._absolute_url(name_link.get("href", "") if name_link else ""),
            "email_verification": self._text_or_empty(row.find("div", class_="gs_ai_eml")),
            "publications": [],
            "source": self.config.base_url,
        }

    def _get_soup(self, path: str, params: dict[str, str]) -> BeautifulSoup:
        response = requests.get(
            urljoin(f"{self.config.base_url}/", path.lstrip("/")),
            params=params,
            headers={"User-Agent": self._USER_AGENT},
            proxies=self._proxies(),
            timeout=self.config.timeout_sec,
        )
        if response.status_code != 200:
            raise ScholarServiceError(
                f"Scholar mirror returned HTTP {response.status_code}: {response.url}"
            )
        return BeautifulSoup(response.text, "html.parser")

    def _parse_publication_results(
        self, soup: BeautifulSoup, num_results: int
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for item in soup.find_all("div", class_="gs_ri"):
            if len(results) >= num_results:
                break
            parsed = self._parse_publication_result(item)
            if parsed["title"] or parsed["publication_url"]:
                results.append(parsed)
        return results

    def _parse_publication_result(self, item: Any) -> dict[str, Any]:
        title_tag = item.find("h3", class_="gs_rt")
        link_tag = title_tag.find("a") if title_tag else None
        authors_text = self._text_or_empty(item.find("div", class_="gs_a"))
        abstract_tag = item.find("div", class_="gs_rs") or item.find("div", class_="gs_snippet")

        citations = 0
        for action_link in item.select("div.gs_fl a"):
            text = self._text_or_empty(action_link)
            if "引用" in text or "cited by" in text.lower():
                citations = self._extract_first_int(text)
                break

        return {
            "title": self._text_or_empty(title_tag),
            "authors": authors_text,
            "abstract": self._text_or_empty(abstract_tag),
            "year": self._extract_year(authors_text),
            "venue": "",
            "citations": citations,
            "publication_url": link_tag.get("href", "") if link_tag else "",
            "scholar_url": "",
            "source": self.config.base_url,
        }

    def _proxies(self) -> dict[str, str] | None:
        if not self.config.http_proxy:
            return None
        return {
            "http": self.config.http_proxy,
            "https": self.config.https_proxy or self.config.http_proxy,
        }

    def _absolute_url(self, url: str) -> str:
        if not url:
            return ""
        return urljoin(f"{self.config.base_url}/", url)

    @staticmethod
    def _text_or_empty(node: Any) -> str:
        if node is None:
            return ""
        return node.get_text(" ", strip=True)

    @staticmethod
    def _extract_first_int(text: str) -> int:
        match = re.search(r"(\d[\d,]*)", text)
        if not match:
            return 0
        return int(match.group(1).replace(",", ""))

    @staticmethod
    def _extract_year(text: str) -> str:
        years = re.findall(r"\b(19|20)\d{2}\b", text)
        if not years:
            return ""
        match = re.search(r"\b((?:19|20)\d{2})\b", text)
        return match.group(1) if match else ""

    @staticmethod
    def _extract_user_id(url: str) -> str:
        if not url:
            return ""
        parsed = urlparse(url)
        return parse_qs(parsed.query).get("user", [""])[0]

    @staticmethod
    def _validate_query(query: str, field_name: str = "query") -> str:
        value = query.strip()
        if not value:
            raise ValueError(f"{field_name} must not be empty.")
        return value

    @staticmethod
    def _validate_num_results(num_results: int) -> int:
        if not 1 <= num_results <= 20:
            raise ValueError("num_results must be between 1 and 20.")
        return num_results

    @staticmethod
    def _normalize_year_range(
        start_year: int | None,
        end_year: int | None,
    ) -> tuple[int | None, int | None]:
        if start_year is None and end_year is None:
            return None, None

        year_low = int(start_year) if start_year is not None else None
        year_high = int(end_year) if end_year is not None else None
        if year_low is None or year_high is None:
            raise ValueError("start_year and end_year must be provided together.")
        if year_low > year_high:
            raise ValueError("start_year must be less than or equal to end_year.")
        return year_low, year_high

    @staticmethod
    def _normalize_search_in(search_in: str) -> str:
        normalized = search_in.strip().lower() or "anywhere"
        allowed = {
            "anywhere": "any",
            "any": "any",
            "title": "title",
        }
        if normalized not in allowed:
            raise ValueError("search_in must be either 'anywhere' or 'title'.")
        return allowed[normalized]
