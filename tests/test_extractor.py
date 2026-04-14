import unittest

from commonplace_app.extractor import _extract_structured_data, _load_json_loose


class ExtractorTests(unittest.TestCase):
    def test_extracts_from_parsed_output(self):
        body = {
            "output": [
                {
                    "type": "message",
                    "content": [
                        {
                            "type": "output_text",
                            "parsed": {"title": "Session", "summary": "Summary"},
                        }
                    ],
                }
            ]
        }
        self.assertEqual(_extract_structured_data(body), {"title": "Session", "summary": "Summary"})

    def test_extracts_from_text_json(self):
        body = {
            "output": [
                {
                    "type": "message",
                    "content": [
                        {
                            "type": "output_text",
                            "text": '{"title":"Session","summary":"Summary"}',
                        }
                    ],
                }
            ]
        }
        self.assertEqual(_extract_structured_data(body), {"title": "Session", "summary": "Summary"})

    def test_falls_back_to_function_call_arguments(self):
        body = {
            "output": [
                {
                    "type": "function_call",
                    "arguments": '{"title":"Session","summary":"Summary"}',
                }
            ]
        }
        self.assertEqual(_extract_structured_data(body), {"title": "Session", "summary": "Summary"})

    def test_load_json_loose_finds_embedded_object(self):
        text = "Here is the JSON:\n{\"title\":\"Session\",\"summary\":\"Summary\"}"
        self.assertEqual(_load_json_loose(text), {"title": "Session", "summary": "Summary"})


if __name__ == "__main__":
    unittest.main()
