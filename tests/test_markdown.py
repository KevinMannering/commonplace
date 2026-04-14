from datetime import datetime, timezone
import unittest

from commonplace_app.markdown import render_markdown


class MarkdownTests(unittest.TestCase):
    def test_strategy_markdown_renders_sections(self):
        data = {
            "title": "Strategy Session",
            "summary": "We decided to start with one command.",
            "decisions": [{"decision": "Ship CLI first", "reasoning": "Fastest path to proving value."}],
            "assumptions": [{"assumption": "Users will supply transcripts", "reasoning": "No ingestion system yet."}],
            "challenges": [{"challenge": "Transcript quality varies", "why_it_matters": "Extraction quality depends on it."}],
            "open_questions": [{"question": "How should titles be standardized?", "why_open": "No naming convention yet."}],
            "pivots": [{"from_position": "Build UI first", "to_position": "Start with CLI", "why_it_changed": "Phase 1 scope needed to stay narrow."}],
            "named_concepts": [{"name": "Victorian Library", "description": "A curated personal knowledge system."}],
        }
        markdown = render_markdown(
            data=data,
            session_type="strategy",
            transcript_path="transcript.md",
            model="gpt-5.4",
            generated_at=datetime(2026, 4, 13, 12, 0, 0, tzinfo=timezone.utc),
        )
        self.assertIn("## Key Decisions", markdown)
        self.assertIn("## Open Questions", markdown)
        self.assertIn("[[Victorian Library]]", markdown)

    def test_research_markdown_renders_sections(self):
        data = {
            "title": "Research Session",
            "summary": "We mapped the landscape.",
            "claims": [{"claim": "Memory compounds usage", "reasoning": "Users revisit prior thinking."}],
            "evidence": [{"point": "Repeated session resets are frustrating", "supports": "Need for continuity."}],
            "sources": [{"source": "User interviews", "relevance": "Primary signal for the pain point."}],
            "gaps": [{"gap": "No quantified retention data", "why_it_matters": "Cannot size impact yet."}],
            "conclusions": [{"conclusion": "Phase 1 should be CLI only", "basis": "Smallest testable wedge."}],
            "pivots": [],
            "named_concepts": [],
        }
        markdown = render_markdown(
            data=data,
            session_type="research",
            transcript_path="transcript.md",
            model="gpt-5.4",
        )
        self.assertIn("## Claims", markdown)
        self.assertIn("## Conclusions", markdown)


if __name__ == "__main__":
    unittest.main()
