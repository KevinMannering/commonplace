import unittest
from unittest import mock

from commonplace_app.service import generate_wiki_markdown


class ServiceTests(unittest.TestCase):
    def test_generate_wiki_markdown_returns_markdown_and_metadata(self):
        extracted = {
            "title": "Commonplace Session",
            "summary": "Summary",
            "decisions": [],
            "assumptions": [],
            "challenges": [],
            "open_questions": [],
            "pivots": [],
            "named_concepts": [],
            "_model": "gpt-5.4",
        }

        with mock.patch("commonplace_app.service.extract_session", return_value=extracted):
            result = generate_wiki_markdown(
                transcript="User: hi",
                session_type="strategy",
                title_hint="Hint",
                transcript_source="browser-extension",
            )

        self.assertEqual(result["title"], "Commonplace Session")
        self.assertIn("# Commonplace Session", result["markdown"])
        self.assertIn("browser-extension", result["markdown"])
        self.assertEqual(result["model"], "gpt-5.4")


if __name__ == "__main__":
    unittest.main()
