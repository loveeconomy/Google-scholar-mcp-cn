import unittest
from unittest.mock import patch

from google_scholar_mcp_server.client import GoogleScholarClient, ScholarConfig, ScholarServiceError


class MockResponse:
    def __init__(self, text: str, status_code: int = 200, url: str = "https://scholar.lanfanshu.cn"):
        self.text = text
        self.status_code = status_code
        self.url = url


SEARCH_HTML = """
<html><body>
  <div class="gs_ri">
    <h3 class="gs_rt"><a href="https://example.com/paper">Deep learning</a></h3>
    <div class="gs_a">Y LeCun, Y Bengio, G Hinton - Nature, 2015 - nature.com</div>
    <div class="gs_rs">A paper about deep learning.</div>
    <div class="gs_fl"><a href="#">被引用次数：108766</a></div>
  </div>
</body></html>
"""

AUTHOR_HTML = """
<html><body>
  <div class="gsc_1usr">
    <div class="gs_ai_t">
      <h3 class="gs_ai_name"><a href="/citations?hl=zh-CN&user=JicYPdAAAAAJ">Geoffrey Hinton</a></h3>
      <div class="gs_ai_aff">Emeritus Prof. Computer Science, University of Toronto</div>
      <div class="gs_ai_eml">在 cs.toronto.edu 的电子邮件经过验证</div>
      <div class="gs_ai_cby">被引用次数：834104</div>
      <div class="gs_ai_int">
        <a class="gs_ai_one_int" href="#">machine learning</a>
        <a class="gs_ai_one_int" href="#">psychology</a>
      </div>
    </div>
  </div>
</body></html>
"""


class GoogleScholarClientTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = ScholarConfig(
            base_url="https://scholar.lanfanshu.cn",
            timeout_sec=1,
            author_publication_limit=2,
        )

    @patch("google_scholar_mcp_server.client.requests.get")
    def test_search_keywords_formats_results(self, get_mock) -> None:
        get_mock.return_value = MockResponse(SEARCH_HTML)

        client = GoogleScholarClient(self.config)
        result = client.search_keywords("deep learning", 1)

        self.assertEqual(result[0]["title"], "Deep learning")
        self.assertIn("Hinton", result[0]["authors"])
        self.assertEqual(result[0]["year"], "2015")
        self.assertEqual(result[0]["citations"], 108766)
        self.assertEqual(result[0]["source"], "https://scholar.lanfanshu.cn")

    @patch("google_scholar_mcp_server.client.requests.get")
    def test_search_advanced_sends_advanced_params(self, get_mock) -> None:
        get_mock.return_value = MockResponse(SEARCH_HTML)

        client = GoogleScholarClient(self.config)
        result = client.search_advanced(
            all_words="forecast system",
            exact_phrase="systems engineering",
            any_words="prediction forecasting",
            exclude_words="stock",
            search_in="title",
            author="Wang",
            publication="系统工程",
            start_year=2025,
            end_year=2025,
            num_results=3,
        )

        self.assertEqual(len(result), 1)
        _, kwargs = get_mock.call_args
        self.assertEqual(kwargs["params"]["as_q"], "forecast system")
        self.assertEqual(kwargs["params"]["as_epq"], "systems engineering")
        self.assertEqual(kwargs["params"]["as_oq"], "prediction forecasting")
        self.assertEqual(kwargs["params"]["as_eq"], "stock")
        self.assertEqual(kwargs["params"]["as_occt"], "title")
        self.assertEqual(kwargs["params"]["as_sauthors"], "Wang")
        self.assertEqual(kwargs["params"]["as_publication"], "系统工程")
        self.assertEqual(kwargs["params"]["as_ylo"], "2025")
        self.assertEqual(kwargs["params"]["as_yhi"], "2025")

    def test_search_advanced_requires_valid_search_in(self) -> None:
        client = GoogleScholarClient(self.config)

        with self.assertRaises(ValueError):
            client.search_advanced(all_words="test", search_in="abstract")

    @patch("google_scholar_mcp_server.client.requests.get")
    def test_get_author_info_parses_summary_row(self, get_mock) -> None:
        get_mock.return_value = MockResponse(AUTHOR_HTML)

        client = GoogleScholarClient(self.config)
        result = client.get_author_info("Geoffrey Hinton")

        self.assertEqual(result["name"], "Geoffrey Hinton")
        self.assertEqual(result["cited_by"], 834104)
        self.assertEqual(result["scholar_id"], "JicYPdAAAAAJ")
        self.assertEqual(result["publications"], [])


if __name__ == "__main__":
    unittest.main()
