"""Tests for the local Commonplace web UI."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
import re
import shutil
import subprocess

from fastapi.testclient import TestClient

from commonplace import cli
from commonplace.ui import app as ui_app


def create_test_app(tmp_path: Path, monkeypatch) -> TestClient:
    repo_root = tmp_path.resolve()
    book_dir = (repo_root / "book").resolve()
    inbox_dir = (repo_root / "inbox").resolve()
    sources_dir = (repo_root / "sources" / "incoming").resolve()
    book_dir.mkdir(parents=True)
    inbox_dir.mkdir(parents=True)
    sources_dir.mkdir(parents=True)
    (book_dir / "_index.md").write_text("index", encoding="utf-8")
    (book_dir / "_topics.md").write_text("topics", encoding="utf-8")
    (book_dir / "README.md").write_text("scaffold", encoding="utf-8")
    (book_dir / "CONVENTIONS.md").write_text("scaffold", encoding="utf-8")
    (book_dir / "OpenClaw & AI Agentic Systems — Knowledge Base.md").write_text(
        "---\n"
        "title: OpenClaw & AI Agentic Systems — Knowledge Base\n"
        "kind: field-study\n"
        "why-kept: Canonical field entry.\n"
        "topics: [openclaw, agent-architecture]\n"
        "related-entries:\n"
        "  - Agent Economics Notes\n"
        "---\n\n"
        "# OpenClaw\n",
        encoding="utf-8",
    )
    (book_dir / "Agent Economics Notes.md").write_text(
        "---\n"
        "title: Agent Economics Notes\n"
        "kind: idea-study\n"
        "why-kept: Tracks economic patterns in agent infrastructure.\n"
        "topics: [agent-economics, ai-investment]\n"
        "---\n\n"
        "# Agent Economics Notes\n\n"
        "Pricing, margins, and infrastructure moats.\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(cli, "REPO_ROOT", repo_root)
    monkeypatch.setattr(cli, "BOOK_DIR", book_dir)
    monkeypatch.setattr(cli, "INBOX_DIR", inbox_dir)
    monkeypatch.setattr(ui_app, "SOURCES_DIR", sources_dir)
    return TestClient(ui_app.create_app())


def write_inbox_file(
    inbox_dir: Path,
    filename: str,
    action: str,
    extra: str = "",
    annotation: str | None = None,
) -> Path:
    path = inbox_dir / filename
    target_line = (
        '  target_entry: "OpenClaw & AI Agentic Systems — Knowledge Base"\n'
        if action == "append-to"
        else ""
    )
    annotation_line = f'  annotation: "{annotation}"\n' if annotation else ""
    path.write_text(
        "---\n"
        "proposal:\n"
        f"  action: {action}\n"
        '  title: "Test Proposal"\n'
        "  kind: idea-study\n"
        "  topics: [agent-architecture, openclaw]\n"
        "  why_kept: |\n"
        "    Worth keeping.\n"
        f"{annotation_line}"
        f"{target_line}"
        "  reasoning: |\n"
        "    Because.\n"
        "  confidence: medium\n"
        "  needs_escalation: false\n"
        "  escalation_triggers: [low-confidence]\n"
        "source:\n"
        '  file: "source.pdf"\n'
        '  source_path: "/tmp/source.pdf"\n'
        "---\n\n"
        "# Test Proposal\n\n"
        "Body.\n"
        f"{extra}",
        encoding="utf-8",
    )
    return path


def test_root_renders_and_inbox_json_lists_items(tmp_path: Path, monkeypatch) -> None:
    client = create_test_app(tmp_path, monkeypatch)
    inbox_dir = cli.INBOX_DIR
    write_inbox_file(inbox_dir, "2026-04-30-test.md", "new-entry")

    response = client.get("/")
    assert response.status_code == 200
    assert "Test Proposal" in response.text

    json_response = client.get("/inbox")
    payload = json_response.json()
    assert payload["items"][0]["title"] == "Test Proposal"
    assert payload["inbox_count"] == 1


def test_root_inline_script_is_valid_javascript(tmp_path: Path, monkeypatch) -> None:
    node = shutil.which("node")
    if node is None:
        return

    client = create_test_app(tmp_path, monkeypatch)
    write_inbox_file(cli.INBOX_DIR, "2026-04-30-test.md", "new-entry")

    response = client.get("/")
    assert response.status_code == 200

    match = re.search(r"<script>\s*(.*?)\s*</script>", response.text, re.DOTALL)
    assert match is not None

    compiled = subprocess.run(
        [node, "-e", "new Function(process.argv[1]);", match.group(1)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert compiled.returncode == 0, compiled.stderr


def test_detail_endpoint_handles_new_entry_and_append_to(tmp_path: Path, monkeypatch) -> None:
    client = create_test_app(tmp_path, monkeypatch)
    inbox_dir = cli.INBOX_DIR
    write_inbox_file(inbox_dir, "new.md", "new-entry")
    write_inbox_file(inbox_dir, "append.md", "append-to")

    new_detail = client.get("/inbox/new.md").json()
    append_detail = client.get("/inbox/append.md").json()

    assert new_detail["proposal"]["action"] == "new-entry"
    assert new_detail["resolved_target_entry_path"] is None
    assert append_detail["proposal"]["action"] == "append-to"
    assert append_detail["resolved_target_entry_path"].endswith(
        "OpenClaw & AI Agentic Systems — Knowledge Base.md"
    )


def test_book_entries_endpoint_excludes_scaffold_files(tmp_path: Path, monkeypatch) -> None:
    client = create_test_app(tmp_path, monkeypatch)
    (cli.BOOK_DIR / "Fresh Entry.md").write_text(
        "---\n"
        "title: Fresh Entry\n"
        "kind: thinker\n"
        "why-kept: Useful.\n"
        "topics: [fresh]\n"
        "---\n\n"
        "# Fresh Entry\n",
        encoding="utf-8",
    )

    response = client.get("/book/entries")
    payload = response.json()
    titles = [entry["title"] for entry in payload["entries"]]

    assert response.status_code == 200
    assert "OpenClaw & AI Agentic Systems — Knowledge Base" in titles
    assert "Fresh Entry" in titles
    assert "README" not in titles
    assert "CONVENTIONS" not in titles


def test_book_detail_endpoint_returns_canonical_entry_summary(tmp_path: Path, monkeypatch) -> None:
    client = create_test_app(tmp_path, monkeypatch)

    response = client.get("/book/Agent%20Economics%20Notes.md")
    payload = response.json()

    assert response.status_code == 200
    assert payload["entry"]["title"] == "Agent Economics Notes"
    assert payload["entry"]["kind"] == "idea-study"
    assert "agent-economics" in payload["entry"]["topics"]
    assert "<h1>Agent Economics Notes</h1>" in payload["body_html"]


def test_book_annotations_can_be_updated(tmp_path: Path, monkeypatch) -> None:
    client = create_test_app(tmp_path, monkeypatch)

    response = client.put(
        "/book/Agent%20Economics%20Notes.md/annotations",
        json={"annotations": "This is the market map.\nWatch pricing compression."},
    )
    payload = response.json()
    saved_text = (cli.BOOK_DIR / "Agent Economics Notes.md").read_text(encoding="utf-8")

    assert response.status_code == 200
    assert payload["entry"]["annotations"] == [
        "This is the market map.",
        "Watch pricing compression.",
    ]
    assert "annotations:" in saved_text
    assert "This is the market map." in saved_text


def test_chat_endpoint_uses_stubbed_answer(tmp_path: Path, monkeypatch) -> None:
    client = create_test_app(tmp_path, monkeypatch)

    def fake_answer(query: str, client=None) -> dict[str, object]:
        assert query == "How does OpenClaw fit into agent architecture?"
        return {
            "answer": "**OpenClaw** sits in the agent architecture layer.",
            "answer_html": "<p><strong>OpenClaw</strong> sits in the agent architecture layer.</p>",
            "matched_entries": [
                {
                    "filename": "OpenClaw & AI Agentic Systems — Knowledge Base.md",
                    "title": "OpenClaw & AI Agentic Systems — Knowledge Base",
                    "kind": "field-study",
                    "topics": ["openclaw", "agent-architecture"],
                    "related_entries": ["Agent Economics Notes"],
                }
            ],
            "model": "test-model",
        }

    monkeypatch.setattr(ui_app, "answer_commonplace_query", fake_answer)

    response = client.post("/chat", json={"query": "How does OpenClaw fit into agent architecture?"})
    payload = response.json()

    assert response.status_code == 200
    assert payload["answer"] == "**OpenClaw** sits in the agent architecture layer."
    assert "<strong>OpenClaw</strong>" in payload["answer_html"]
    assert payload["matched_entries"][0]["title"] == "OpenClaw & AI Agentic Systems — Knowledge Base"


def test_chat_router_prefers_metadata_matches_and_expands_related_entries(tmp_path: Path, monkeypatch) -> None:
    create_test_app(tmp_path, monkeypatch)
    entries = ui_app.load_chat_book_entries()

    matched = ui_app.route_query_to_entries(
        "What does the book say about OpenClaw and agent architecture?",
        entries,
    )

    titles = [entry.title for entry in matched]
    assert titles[0] == "OpenClaw & AI Agentic Systems — Knowledge Base"
    assert "Agent Economics Notes" in titles


def test_build_chat_prompt_asks_for_labeled_inference_when_direct_match_is_missing() -> None:
    entry = ui_app.ChatBookEntry(
        path=Path("Catalog Entry.md"),
        title="Catalog Entry",
        kind="field-study",
        why_kept="Tracks how the book reasons about infrastructure.",
        topics=["infrastructure", "agents"],
        related_entries=["Agent Economics Notes"],
        annotations=["Watch how standards form."],
        body=None,
    )

    prompt = ui_app.build_chat_prompt(
        query="What would the book think about a new protocol market?",
        entries=[entry],
        mode="catalog-inference",
    )

    assert "does not appear to contain a directly matched entry" in prompt
    assert "first say that the book does not directly address it" in prompt
    assert "clearly labeled inference" in prompt
    assert "Commonplace catalog snapshot:" in prompt


def test_query_requests_annotations_detects_notes_and_point_of_view_language() -> None:
    assert ui_app.query_requests_annotations("What do my annotations say about this?") is True
    assert ui_app.query_requests_annotations("What is my point of view here?") is True
    assert ui_app.query_requests_annotations("Summarize the notes on this entry") is True
    assert ui_app.query_requests_annotations("How does OpenClaw fit into agent architecture?") is False


def test_build_chat_prompt_adds_annotation_pov_context_when_requested() -> None:
    entry = ui_app.ChatBookEntry(
        path=Path("Agent Economics Notes.md"),
        title="Agent Economics Notes",
        kind="idea-study",
        why_kept="Tracks economic patterns in agent infrastructure.",
        topics=["agent-economics", "ai-investment"],
        related_entries=["OpenClaw & AI Agentic Systems — Knowledge Base"],
        annotations=["This is the market map.", "Watch pricing compression."],
        body="Pricing, margins, and infrastructure moats.",
    )

    prompt = ui_app.build_chat_prompt(
        query="What do my annotations suggest is my point of view on this?",
        entries=[entry],
        mode="matched-entries",
        emphasize_annotations=True,
    )

    assert "The user is explicitly asking about notes, annotations, or point of view." in prompt
    assert "User point-of-view from annotations:" in prompt
    assert "Treat these notes as the clearest available signal" in prompt
    assert "- Agent Economics Notes: This is the market map. | Watch pricing compression." in prompt


def test_build_chat_prompt_handles_annotation_request_without_any_saved_notes() -> None:
    entry = ui_app.ChatBookEntry(
        path=Path("Catalog Entry.md"),
        title="Catalog Entry",
        kind="field-study",
        why_kept="Tracks how the book reasons about infrastructure.",
        topics=["infrastructure", "agents"],
        related_entries=[],
        annotations=[],
        body=None,
    )

    prompt = ui_app.build_chat_prompt(
        query="What is my point of view here?",
        entries=[entry],
        mode="matched-entries",
        emphasize_annotations=True,
    )

    assert "(No explicit annotations were supplied for these entries." in prompt


def test_answer_commonplace_query_uses_catalog_inference_when_no_entry_matches(tmp_path: Path, monkeypatch) -> None:
    create_test_app(tmp_path, monkeypatch)

    class FakeResponses:
        def __init__(self) -> None:
            self.captured_input = None

        def create(self, *, model, input):
            self.captured_input = input
            return type(
                "Response",
                (),
                {
                    "output": [
                        type(
                            "Message",
                            (),
                            {
                                "type": "message",
                                "content": [
                                    type(
                                        "OutputText",
                                        (),
                                        {
                                            "type": "output_text",
                                            "text": (
                                                "The book does not directly address that yet.\n\n"
                                                "Possible inference from the book's current concerns: "
                                                "it would likely examine market structure, standards, and moats."
                                            ),
                                        },
                                    )()
                                ],
                            },
                        )()
                    ]
                },
            )()

    class FakeClient:
        def __init__(self) -> None:
            self.responses = FakeResponses()

    fake_client = FakeClient()
    answer = ui_app.answer_commonplace_query(
        query="What would the book think about decentralized sensor markets?",
        client=fake_client,
    )

    user_prompt = fake_client.responses.captured_input[1]["content"]
    assert "does not appear to contain a directly matched entry" in user_prompt
    assert "Commonplace catalog snapshot:" in user_prompt
    assert answer["matched_entries"] == []
    assert "does not directly address" in answer["answer"]
    assert answer["model"] == ui_app.CHAT_MODEL


def test_answer_commonplace_query_includes_annotation_pov_when_query_targets_notes(tmp_path: Path, monkeypatch) -> None:
    create_test_app(tmp_path, monkeypatch)

    class FakeResponses:
        def __init__(self) -> None:
            self.captured_input = None

        def create(self, *, model, input):
            self.captured_input = input
            return type(
                "Response",
                (),
                {
                    "output": [
                        type(
                            "Message",
                            (),
                            {
                                "type": "message",
                                "content": [
                                    type(
                                        "OutputText",
                                        (),
                                        {
                                            "type": "output_text",
                                            "text": "Your notes emphasize market structure and pricing pressure.",
                                        },
                                    )()
                                ],
                            },
                        )()
                    ]
                },
            )()

    class FakeClient:
        def __init__(self) -> None:
            self.responses = FakeResponses()

    fake_client = FakeClient()
    answer = ui_app.answer_commonplace_query(
        query="What do my annotations say about agent economics?",
        client=fake_client,
    )

    user_prompt = fake_client.responses.captured_input[1]["content"]
    assert "User point-of-view from annotations:" in user_prompt
    assert "The user is explicitly asking about notes, annotations, or point of view." in user_prompt
    assert answer["answer"] == "Your notes emphasize market structure and pricing pressure."


def test_put_inbox_updates_editable_fields_and_preserves_audit_fields(tmp_path: Path, monkeypatch) -> None:
    client = create_test_app(tmp_path, monkeypatch)
    write_inbox_file(cli.INBOX_DIR, "edit.md", "new-entry")

    response = client.put(
        "/inbox/edit.md",
        json={
            "title": "Edited Proposal",
            "kind": "field-study",
            "topics": "edited, focused",
            "why_kept": "Still worth keeping.",
            "annotation": "I want to remember the framing shift here.",
            "action": "new-entry",
            "target_entry": "should be ignored",
            "body": "# Edited Proposal\n\nRewritten body.\n",
        },
    )
    payload = response.json()
    saved_text = (cli.INBOX_DIR / "edit.md").read_text(encoding="utf-8")

    assert response.status_code == 200
    assert payload["proposal"]["title"] == "Edited Proposal"
    assert payload["proposal"]["kind"] == "field-study"
    assert payload["proposal"]["topics"] == ["edited", "focused"]
    assert payload["proposal"]["why_kept"] == "Still worth keeping."
    assert payload["proposal"]["annotation"] == "I want to remember the framing shift here."
    assert payload["proposal"]["action"] == "new-entry"
    assert payload["proposal"]["target_entry"] is None
    assert payload["body_markdown"] == "# Edited Proposal\n\nRewritten body.\n"
    assert payload["proposal"]["last_edited_at"]
    assert payload["proposal"]["confidence"] == "medium"
    assert payload["proposal"]["needs_escalation"] is False
    assert payload["source"]["source_path"] == "/tmp/source.pdf"
    assert "last_edited_at:" in saved_text
    assert "escalation_triggers:" in saved_text
    assert "source_path: /tmp/source.pdf" in saved_text


def test_put_inbox_allows_annotation_only_update(tmp_path: Path, monkeypatch) -> None:
    client = create_test_app(tmp_path, monkeypatch)
    write_inbox_file(cli.INBOX_DIR, "annotate.md", "new-entry")

    response = client.put(
        "/inbox/annotate.md",
        json={"annotation": "This is the connective note I want to preserve."},
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["proposal"]["annotation"] == "This is the connective note I want to preserve."
    assert payload["proposal"]["title"] == "Test Proposal"
    assert payload["proposal"]["action"] == "new-entry"


def test_put_inbox_accepts_capitalized_annotation_key(tmp_path: Path, monkeypatch) -> None:
    client = create_test_app(tmp_path, monkeypatch)
    write_inbox_file(cli.INBOX_DIR, "annotate-case.md", "new-entry")

    response = client.put(
        "/inbox/annotate-case.md",
        json={"Annotation": "Capitalized key should still save."},
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["proposal"]["annotation"] == "Capitalized key should still save."


def test_put_inbox_rejects_unknown_fields_invalid_action_and_bad_append_target(tmp_path: Path, monkeypatch) -> None:
    client = create_test_app(tmp_path, monkeypatch)
    write_inbox_file(cli.INBOX_DIR, "edit.md", "new-entry")

    unknown = client.put("/inbox/edit.md", json={"bogus": "value"})
    assert unknown.status_code == 400
    assert "Unknown editable fields" in unknown.json()["detail"]

    invalid_action = client.put("/inbox/edit.md", json={"action": "merge-into"})
    assert invalid_action.status_code == 400
    assert "Invalid action" in invalid_action.json()["detail"]

    missing_target = client.put("/inbox/edit.md", json={"action": "append-to"})
    assert missing_target.status_code == 400
    assert "require a valid target_entry" in missing_target.json()["detail"]

    bad_target = client.put(
        "/inbox/edit.md",
        json={"action": "append-to", "target_entry": "Missing Entry"},
    )
    assert bad_target.status_code == 400
    assert "Unknown target_entry" in bad_target.json()["detail"]


def test_put_inbox_switch_to_append_to_then_promote_appends_to_target(tmp_path: Path, monkeypatch) -> None:
    client = create_test_app(tmp_path, monkeypatch)
    target_path = cli.BOOK_DIR / "OpenClaw & AI Agentic Systems — Knowledge Base.md"
    original_target_text = target_path.read_text(encoding="utf-8")
    write_inbox_file(cli.INBOX_DIR, "switch.md", "new-entry")

    update = client.put(
        "/inbox/switch.md",
        json={
            "title": "Append This",
            "kind": "idea-study",
            "topics": ["agent-architecture", "openclaw"],
            "why_kept": "Append it.",
            "annotation": "Useful connective tissue for the OpenClaw knowledge base.",
            "action": "append-to",
            "target_entry": "OpenClaw & AI Agentic Systems — Knowledge Base",
            "body": "## Appended Section\n\nAdded from edited inbox proposal.\n",
        },
    )
    assert update.status_code == 200

    promote = client.post("/inbox/switch.md/promote", json={"copy": False})
    assert promote.status_code == 200
    updated_target_text = target_path.read_text(encoding="utf-8")

    assert not (cli.INBOX_DIR / "switch.md").exists()
    assert "## Appended Section" in updated_target_text
    assert "Added from edited inbox proposal." in updated_target_text
    assert "Useful connective tissue for the OpenClaw knowledge base." in updated_target_text
    assert "# OpenClaw" in updated_target_text
    assert "related-entries:" in updated_target_text


def test_promote_endpoint_and_flag_for_judgment_refusal(tmp_path: Path, monkeypatch) -> None:
    client = create_test_app(tmp_path, monkeypatch)
    inbox_dir = cli.INBOX_DIR
    write_inbox_file(inbox_dir, "new.md", "new-entry", annotation="Worth keeping for later recall.")
    write_inbox_file(inbox_dir, "flag.md", "flag-for-judgment")

    ok_response = client.post("/inbox/new.md/promote", json={"copy": False})
    assert ok_response.status_code == 200
    assert (cli.BOOK_DIR / "new.md").exists()

    refused = client.post("/inbox/flag.md/promote", json={"copy": False})
    assert refused.status_code == 400
    assert "flag-for-judgment" in refused.json()["detail"]


def test_promote_endpoint_requires_annotation(tmp_path: Path, monkeypatch) -> None:
    client = create_test_app(tmp_path, monkeypatch)
    write_inbox_file(cli.INBOX_DIR, "missing-annotation.md", "new-entry")

    response = client.post("/inbox/missing-annotation.md/promote", json={"copy": False})

    assert response.status_code == 400
    assert "Cannot promote without an annotation" in response.json()["detail"]


def test_discard_moves_file_into_dated_archive(tmp_path: Path, monkeypatch) -> None:
    client = create_test_app(tmp_path, monkeypatch)
    inbox_dir = cli.INBOX_DIR
    proposal = write_inbox_file(inbox_dir, "discard.md", "new-entry")

    response = client.post("/inbox/discard.md/discard")
    archive_path = Path(response.json()["archived_to"])

    assert response.status_code == 200
    assert archive_path.exists()
    assert not proposal.exists()
    assert "_archive" in archive_path.parts


def test_sync_book_endpoint_returns_summary(tmp_path: Path, monkeypatch) -> None:
    client = create_test_app(tmp_path, monkeypatch)
    write_inbox_file(cli.INBOX_DIR, "sync.md", "new-entry")

    response = client.post("/sync-book")
    payload = response.json()

    assert response.status_code == 200
    assert payload["index_path"].endswith("_index.md")
    assert payload["topics_path"].endswith("_topics.md")


def test_ingest_endpoint_handles_success_multi_file_and_validation(tmp_path: Path, monkeypatch) -> None:
    client = create_test_app(tmp_path, monkeypatch)

    def fake_run_ingest(path: str, message: str | None = None, model: str = "") -> Path:
        saved_path = Path(path)
        inbox_path = cli.INBOX_DIR / f"{saved_path.stem}.md"
        inbox_path.write_text(
            "---\nproposal:\n  action: new-entry\n  title: \"Uploaded\"\n  kind: idea-study\n"
            "  topics: [upload, test]\n  why_kept: |\n    Useful.\n  reasoning: |\n    Because.\n"
            "  confidence: high\n  needs_escalation: false\nsource:\n  file: \"source\"\n---\n\n# Uploaded\n",
            encoding="utf-8",
        )
        return inbox_path

    monkeypatch.setattr(cli, "run_ingest", fake_run_ingest)

    single = client.post(
        "/ingest",
        files=[("files", ("single.pdf", BytesIO(b"pdf-bytes"), "application/pdf"))],
    )
    single_payload = single.json()["results"][0]
    assert single.status_code == 200
    assert single_payload["inbox_filename"] == "single.md"
    assert Path(single_payload["saved_source_path"]).exists()

    multi = client.post(
        "/ingest",
        files=[
            ("files", ("first.pdf", BytesIO(b"first"), "application/pdf")),
            ("files", ("second.md", BytesIO(b"# second"), "text/markdown")),
        ],
    )
    multi_payload = multi.json()["results"]
    assert len(multi_payload) == 2
    assert multi_payload[0]["error"] is None
    assert multi_payload[1]["error"] is None

    rejected = client.post(
        "/ingest",
        files=[("files", ("bad.txt", BytesIO(b"bad"), "text/plain"))],
    )
    assert "Unsupported upload type" in rejected.json()["results"][0]["error"]

    oversize = client.post(
        "/ingest",
        files=[("files", ("huge.pdf", BytesIO(b"x" * ((25 * 1024 * 1024) + 1)), "application/pdf"))],
    )
    assert "25 MB limit" in oversize.json()["results"][0]["error"]

    def failing_run_ingest(path: str, message: str | None = None, model: str = "") -> Path:
        raise RuntimeError("ingest failed")

    monkeypatch.setattr(cli, "run_ingest", failing_run_ingest)
    failed = client.post(
        "/ingest",
        files=[("files", ("broken.pdf", BytesIO(b"broken"), "application/pdf"))],
    )
    assert failed.json()["results"][0]["error"] == "ingest failed"
