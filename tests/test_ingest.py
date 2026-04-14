import unittest

from commonplace_app.ingest import extract_transcript_from_html, is_url


class IngestTests(unittest.TestCase):
    def test_is_url(self):
        self.assertTrue(is_url("https://chatgpt.com/share/abc"))
        self.assertTrue(is_url("https://claude.ai/share/abc"))
        self.assertFalse(is_url("transcript.md"))

    def test_extracts_structured_messages_from_embedded_json(self):
        html = """
        <html>
          <head><title>Strategy Chat</title></head>
          <body>
            <script>
              {"messages": [
                {"role": "user", "content": "We should start with a single command."},
                {"role": "assistant", "content": "Agreed. Keep Phase 1 tightly scoped."}
              ]}
            </script>
          </body>
        </html>
        """
        transcript, title_hint = extract_transcript_from_html(html, "https://chatgpt.com/share/abc")
        self.assertEqual(title_hint, "Strategy Chat")
        self.assertIn("User: We should start with a single command.", transcript)
        self.assertIn("Assistant: Agreed. Keep Phase 1 tightly scoped.", transcript)

    def test_falls_back_to_visible_text(self):
        html = """
        <html>
          <head><title>Claude Share</title></head>
          <body>
            <main>
              <div>Should Commonplace accept shared links?</div>
              <div>Yes, because that is the lowest-friction input path.</div>
            </main>
          </body>
        </html>
        """
        transcript, title_hint = extract_transcript_from_html(html, "https://claude.ai/share/abc")
        self.assertEqual(title_hint, "Claude Share")
        self.assertIn("Should Commonplace accept shared links?", transcript)
        self.assertIn("lowest-friction input path", transcript)


if __name__ == "__main__":
    unittest.main()
