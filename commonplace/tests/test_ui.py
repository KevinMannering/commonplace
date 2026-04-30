"""Tests for the local Commonplace web UI."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

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
        "---\n\n"
        "# OpenClaw\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(cli, "REPO_ROOT", repo_root)
    monkeypatch.setattr(cli, "BOOK_DIR", book_dir)
    monkeypatch.setattr(cli, "INBOX_DIR", inbox_dir)
    monkeypatch.setattr(ui_app, "SOURCES_DIR", sources_dir)
    return TestClient(ui_app.create_app())


def write_inbox_file(inbox_dir: Path, filename: str, action: str, extra: str = "") -> Path:
    path = inbox_dir / filename
    target_line = (
        '  target_entry: "OpenClaw & AI Agentic Systems — Knowledge Base"\n'
        if action == "append-to"
        else ""
    )
    path.write_text(
        "---\n"
        "proposal:\n"
        f"  action: {action}\n"
        '  title: "Test Proposal"\n'
        "  kind: idea-study\n"
        "  topics: [agent-architecture, openclaw]\n"
        "  why_kept: |\n"
        "    Worth keeping.\n"
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
    assert updated_target_text.startswith(original_target_text.rstrip())


def test_promote_endpoint_and_flag_for_judgment_refusal(tmp_path: Path, monkeypatch) -> None:
    client = create_test_app(tmp_path, monkeypatch)
    inbox_dir = cli.INBOX_DIR
    write_inbox_file(inbox_dir, "new.md", "new-entry")
    write_inbox_file(inbox_dir, "flag.md", "flag-for-judgment")

    ok_response = client.post("/inbox/new.md/promote", json={"copy": False})
    assert ok_response.status_code == 200
    assert (cli.BOOK_DIR / "new.md").exists()

    refused = client.post("/inbox/flag.md/promote", json={"copy": False})
    assert refused.status_code == 400
    assert "flag-for-judgment" in refused.json()["detail"]


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
