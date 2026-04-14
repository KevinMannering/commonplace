import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from commonplace_app import cli


class CliTests(unittest.TestCase):
    def test_slugify(self):
        self.assertEqual(cli.slugify("Victorian Gentleman's Library"), "victorian-gentleman-s-library")

    def test_build_output_path_uses_title(self):
        path = cli.build_output_path(Path("/tmp/wiki"), "A New Thesis")
        self.assertTrue(str(path).endswith("-a-new-thesis.md"))

    def test_main_writes_output(self):
        fake_result = {
            "title": "Commonplace Thesis",
            "generated_at": "2026-04-14T00:00:00+00:00",
            "model": "gpt-5.4",
            "markdown": "# Commonplace Thesis\n\n[[Victorian Library]]\n",
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            transcript_path = Path(temp_dir) / "transcript.txt"
            transcript_path.write_text("User: build a CLI\nAssistant: yes", encoding="utf-8")

            loaded = mock.Mock()
            loaded.transcript = "User: build a CLI\nAssistant: yes"
            loaded.source_label = str(transcript_path)
            loaded.title_hint = ""

            with mock.patch("commonplace_app.cli.load_input", return_value=loaded):
                with mock.patch("commonplace_app.cli.generate_wiki_markdown", return_value=fake_result):
                    exit_code = cli.main(
                        [
                            "extract",
                            "--type",
                            "strategy",
                            "--input",
                            str(transcript_path),
                            "--wiki-dir",
                            str(Path(temp_dir) / "wiki"),
                        ]
                    )

            self.assertEqual(exit_code, 0)
            files = list((Path(temp_dir) / "wiki").glob("*.md"))
            self.assertEqual(len(files), 1)
            contents = files[0].read_text(encoding="utf-8")
            self.assertIn("# Commonplace Thesis", contents)
            self.assertIn("[[Victorian Library]]", contents)

    def test_main_accepts_url_input(self):
        fake_result = {
            "title": "Shared Chat Thesis",
            "generated_at": "2026-04-14T00:00:00+00:00",
            "model": "gpt-5.4",
            "markdown": "source_transcript: https://chatgpt.com/share/example\n",
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            loaded = mock.Mock()
            loaded.transcript = "User: Here is a share link transcript"
            loaded.source_label = "https://chatgpt.com/share/example"
            loaded.title_hint = "Shared chat"

            with mock.patch("commonplace_app.cli.load_input", return_value=loaded):
                with mock.patch("commonplace_app.cli.generate_wiki_markdown", return_value=fake_result):
                    exit_code = cli.main(
                        [
                            "extract",
                            "--type",
                            "research",
                            "--input",
                            "https://chatgpt.com/share/example",
                            "--wiki-dir",
                            str(Path(temp_dir) / "wiki"),
                        ]
                    )

            self.assertEqual(exit_code, 0)
            files = list((Path(temp_dir) / "wiki").glob("*.md"))
            self.assertEqual(len(files), 1)
            contents = files[0].read_text(encoding="utf-8")
            self.assertIn("source_transcript: https://chatgpt.com/share/example", contents)

    def test_load_input_from_stdin_passthrough(self):
        from commonplace_app.ingest import load_input

        with mock.patch("sys.stdin", io.StringIO("hello world")):
            loaded = load_input("-")

        self.assertEqual(loaded.transcript, "hello world")
        self.assertEqual(loaded.source_label, "stdin")


if __name__ == "__main__":
    unittest.main()
