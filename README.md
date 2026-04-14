# Commonplace

Let the Wiki Win.

Commonplace helps you keep the thinking from your best LLM conversations instead of losing it when the chat ends.

Commonplace turns meaningful LLM conversations into durable wiki pages.

It now includes:

- a Chrome extension for Claude and ChatGPT
- a FastAPI server that turns transcripts into markdown wiki pages

Phase 1 only does one job:

- Take a conversation transcript as input
- Extract the important thinking with a schema matched to the session type
- Write a clean markdown page into `wiki/`

## Supported session types

- `strategy`: decisions, assumptions, challenges, open questions
- `research`: claims, evidence, sources, gaps, conclusions

Both session types also capture:

- pivots
- named concepts or frameworks

## Usage

Run from the `commonplace/` directory:

```bash
python3 -m commonplace_app.cli extract --type strategy --input ./examples/strategy-transcript.md
```

Or hand it a shared chat URL directly:

```bash
python3 -m commonplace_app.cli extract --type strategy --input "https://chatgpt.com/share/..."
```

Or pipe a transcript in:

```bash
cat transcript.txt | python3 -m commonplace_app.cli extract --type research --title "Consumer health landscape"
```

`--input` now accepts:

- a local transcript file
- a ChatGPT shared chat URL
- a Claude shared chat URL
- stdin when omitted or set to `-`

## Chrome Extension

The extension lives in `extension/` and supports:

- `https://claude.ai/*`
- `https://chatgpt.com/*`

What it does:

- injects a `Save to Commonplace` button near the conversation input
- prompts for session type and optional title
- scrapes the conversation from the page DOM
- sends it to your configured API endpoint
- downloads the returned markdown wiki page

To load it in Chrome:

```bash
chrome://extensions
```

Then:

- enable Developer Mode
- click `Load unpacked`
- select the `commonplace/extension` folder
- open the extension options page and set your API endpoint and API key

## Server

The API server lives in `server/` and exposes:

```text
POST /extract
```

Request body:

```json
{
  "transcript": "User: ...",
  "session_type": "strategy",
  "title": "Optional title"
}
```

Auth header:

```text
X-API-Key: your_api_key
```

Response body:

```json
{
  "markdown": "# ...",
  "title": "Page title",
  "generated_at": "2026-04-14T00:00:00+00:00"
}
```

Run locally:

```bash
pip install -r server/requirements.txt
export OPENAI_API_KEY=your_openai_key
export COMMONPLACE_SERVER_API_KEY=your_server_key
uvicorn server.main:app --reload
```

This is designed to be deployable on Railway or Fly.io.

## Environment

Set an OpenAI API key before running:

```bash
export OPENAI_API_KEY=your_key_here
```

Optional:

```bash
export COMMONPLACE_MODEL=gpt-5.4
```

## Output

Generated pages are written to:

```text
./wiki/
```

Each page includes:

- frontmatter
- a concise summary
- structured sections based on session type
- wiki-style concept links like `[[Decision Journal]]`

## Development

Run tests:

```bash
python3 -m unittest discover -s tests
```
